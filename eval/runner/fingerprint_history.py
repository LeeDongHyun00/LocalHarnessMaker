"""Prove input-first fingerprint provenance without interpreting executor code."""

import ast
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import shlex
from typing import Any


def line_hashes(texts: list[str]) -> set[str]:
    """Use the audit's whitespace-normalized whole-line comparison."""
    return {hashlib.sha256(' '.join(line.split()).encode()).hexdigest()
            for text in texts for line in text.splitlines()}


def input_texts(commands: list[str], patches: list[str]) -> list[str]:
    """Decode literal authored text, including shell/Python string payloads.

    Patch context and deletions do not establish authorship. Shell and Python
    strings are decoded lexically, with no execution, interpolation or reads.
    """
    result = [line[1:] for patch in patches for line in patch.splitlines()
              if line.startswith('+') and not line.startswith('+++')]
    for command in commands:
        result.append(command)
        try:
            words = shlex.split(command)
        except ValueError:
            words = []
        result.extend(words)
        for text in [command, *words]:
            if '"' not in text and "'" not in text:
                continue  # Ordinary operands cannot contain encoded string payloads.
            try:
                tree = ast.parse(text)
            except (SyntaxError, ValueError, RecursionError):
                continue
            result.extend(node.value for node in ast.walk(tree)
                          if isinstance(node, ast.Constant) and isinstance(node.value, str))
    return result


@dataclass
class Occurrence:
    """Retain hashes and record positions, never source text in audit artifacts."""

    path: Path
    line: int
    timestamp: datetime | None
    authored: set[str]
    output: set[str]
    identity: tuple[str, ...] | None
    signature: tuple[str, str, str] | None
    native: bool
    evidence: dict[str, Any]


class FingerprintHistory:
    """Exempt a line only if a recorded input provably precedes every output.

    Within-file positions are authoritative. Cross-file comparisons use strict
    timestamps or session-scoped duplicate-event anchors. Equal/absent timestamps alone
    never establish cross-file order. Ambiguity retains the fingerprint match.
    """

    def __init__(self, fingerprints: set[str]) -> None:
        self.fingerprints = fingerprints
        self.records: list[Occurrence] = []

    def observe(self, *, path: Path, line: int, event: dict[str, Any], item: dict[str, Any],
                authored: list[str], output: list[str], session: str | None,
                command: str | None, evidence: dict[str, Any]) -> None:
        """Record both phases of a tool event; tool input precedes its result."""
        written = line_hashes(authored) & self.fingerprints
        returned = line_hashes(output) & self.fingerprints
        if not written and not returned:
            return
        timestamp = None
        try:
            value = event.get('timestamp')
            timestamp = datetime.fromisoformat(value.replace('Z', '+00:00')) if isinstance(value, str) else None
            timestamp = timestamp.astimezone(timezone.utc) if timestamp and timestamp.tzinfo else None
        except (ValueError, OverflowError):
            pass
        native = event['type'] in {'response_item', 'event_msg'}
        item_type = item.get('type', '')
        phase = ('command' if item_type == 'command_execution' else
                 'input' if item_type in {'function_call', 'custom_tool_call'} else 'output')
        identifier = item.get('call_id') if phase != 'command' else item.get('id')
        if event['type'] in {'item.started', 'item.updated'}:
            phase += ':' + event['type']
        output_hash = hashlib.sha256('\0'.join(output).encode()).hexdigest()
        identity = ((session, phase, identifier, command, output_hash)
                    if session and isinstance(identifier, str) and identifier and command is not None else None)
        signature = ((session, command, output_hash)
                     if session and command is not None and returned and item_type == 'command_execution' else None)
        self.records.append(Occurrence(path, line, timestamp, written, returned,
                                       identity, signature, native, evidence))

    def matches(self) -> list[dict[str, Any]]:
        """Return output evidence only; an earlier output cannot be laundered."""
        identities: dict[tuple[str, ...], list[int]] = defaultdict(list)
        signatures: dict[tuple[str, str, str], list[int]] = defaultdict(list)
        authors: dict[str, list[int]] = defaultdict(list)
        outputs: dict[str, list[int]] = defaultdict(list)
        positions: dict[int, set[int]] = {i: {i} for i in range(len(self.records))}
        bad_clocks: set[Path] = set()
        last_time: dict[Path, datetime] = {}
        for i, record in enumerate(self.records):
            if record.identity:
                identities[record.identity].append(i)
            if record.signature:
                signatures[record.signature].append(i)
            for fingerprint in record.authored:
                authors[fingerprint].append(i)
            for fingerprint in record.output:
                outputs[fingerprint].append(i)
            if record.timestamp:
                if record.path in last_time and record.timestamp < last_time[record.path]:
                    bad_clocks.add(record.path)
                last_time[record.path] = record.timestamp
        for group in identities.values():
            # Reused IDs within one stream are not unique duplicate anchors.
            if len({self.records[i].path for i in group}) == len(group):
                for i in group:
                    positions[i].update(group)
        for group in signatures.values():
            native = [i for i in group if self.records[i].native]
            # A complete ordered repetition in one native stream can align to
            # the same number of results in a CLI stream. Unequal counts, or
            # repetitions across native files, cannot establish correspondence.
            if native and len({self.records[i].path for i in native}) == 1:
                streams: dict[Path, list[int]] = defaultdict(list)
                for i in group:
                    if not self.records[i].native:
                        streams[self.records[i].path].append(i)
                for values in streams.values():
                    if len(values) == len(native):
                        for a, b in zip(sorted(native, key=lambda i: self.records[i].line),
                                        sorted(values, key=lambda i: self.records[i].line)):
                            positions[a].add(b)
                            positions[b].add(a)

        def before(author: int, output: int) -> bool:
            a, b = self.records[author], self.records[output]
            if a.path == b.path:
                return a.line <= b.line  # The command/input phase precedes its own output.
            for x in positions[author]:
                for y in positions[output]:
                    first, second = self.records[x], self.records[y]
                    if first.path == second.path:
                        if first.line <= second.line:
                            return True
                    elif (first.timestamp and second.timestamp and
                          not {first.path, second.path} & bad_clocks and first.timestamp < second.timestamp):
                        return True
            return False

        exempt = {fingerprint for fingerprint, returned in outputs.items()
                  if any(all(before(author, result) for result in returned)
                         for author in authors[fingerprint])}
        return [dict(record.evidence, marker='private_line_fingerprint') for record in self.records
                if record.output - exempt]
