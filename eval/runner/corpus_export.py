"""Export redacted command-stream regressions (not original-run certifications).

Host usage: python -m eval.runner.corpus_export --private-root "$LHM_PRIVATE_GRADERS"
--private-marker MARKER [--report NAME ...]. Existing records never change unless
--rebaseline RECORD_ID is supplied; changes are printed for review. No graders
are opened. Private-bearing physical JSONL lines are omitted before extraction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any
from urllib.parse import unquote

from eval.runner.audit import PrivateGraders, audit_logs
from eval.runner.javascript_derived import LEX

REPORTS = ('full-a-final3', 'full-harness-final3', 'full-b-recovered2',
           'full-v2-a-regrade', 'full-v2-b', 'full-v2-harness')
# Slash preceded by an identifier is a relative suffix, including placeholder tails.
ABSOLUTE = re.compile(r'(?<![\w./])/(?=[A-Za-z_.~])[^\s\x00"\'`<>;,|(){}\[\]\\]+')


def code_parts(source: str) -> list[tuple[str, bool]]:
    """Distinguish regex literals from paths without interpreting the script."""
    parts: list[tuple[str, bool]] = []
    end = 0
    for token in LEX.finditer(source):
        text = token[0]
        if text.startswith('/') and not text.startswith(('//', '/*')) and len(text) > 1:
            parts.extend([(source[end:token.start()], False), (text, True)])
            end = token.end()
    parts.append((source[end:], False))
    return parts


class BaselineChange(ValueError):
    """Carry only the already-sanitized ID for an intentional review."""


def forbidden_markers() -> tuple[str, ...]:
    """Read private directory names at use time without retaining host locations."""
    return ('<private_root>', *(Path(value).name for key in
            ('LHM_PRIVATE_GRADERS', 'LHM_PRIVATE_V3')
            if (value := os.environ.get(key)) and Path(value).name))


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def content_hash(record: dict[str, Any]) -> str:
    return hashlib.sha256(canonical({k: v for k, v in record.items()
                                     if k not in {'expected', 'content_sha256'}})).hexdigest()


def decoded(text: str) -> str:
    value = unquote(text)
    return re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m[1], 16)), value).replace('\\/', '/')


class Redactor:
    """Replace locations while retaining command syntax and directory relationships."""

    def __init__(self, *, home: Path, temp: Path, repository: Path,
                 runtime: Path, private_roots: list[Path], markers: list[str]) -> None:
        roots = {str(p) for p in private_roots}
        roots |= {str(p.resolve()) for p in private_roots}
        for root in tuple(roots):
            if root.startswith('/private/var/'):
                roots.add(root[len('/private'):])
            if root.startswith('/var/'):
                roots.add('/private' + root)
            if root.startswith(str(home) + '/'):
                roots.add('~' + root[len(str(home)):])
        self.forbidden = tuple(x.casefold() for x in (*roots, *markers, *(p.name for p in private_roots), *forbidden_markers()) if x)
        locations = [(runtime / 'workspace', '__WORKSPACE__'), (runtime, '__RUNTIME__'),
                     (repository, '__REPOSITORY__'), (home, '__HOME__'), (temp, '__TEMP__'),
                     (Path('/private/var/folders'), '__HOST_TEMP__'),
                     (Path('/var/folders'), '__HOST_TEMP__'),
                     (Path('/usr'), '__USR__'), (Path('/bin'), '__BIN__'),
                     (Path('/dev'), '__DEV__')]
        self.locations = sorted([(str(p), label) for p, label in locations], key=lambda x: -len(x[0]))
        self.other: dict[str, str] = {}

    def forbidden_line(self, text: str) -> bool:
        return any(marker in decoded(text).casefold() for marker in self.forbidden)

    def text(self, value: str, *, code: bool = False) -> str:
        if code:
            return ''.join(part if regex else self.text(part) for part, regex in code_parts(value))
        for path, label in self.locations:
            value = re.sub(re.escape(path) + r'(?=/|[^\w.-]|$)', lambda _: label, value)
        def replace(match: re.Match[str]) -> str:
            path = match[0]
            return self.other.setdefault(path, f'__PATH_{len(self.other):04d}__')
        return ABSOLUTE.sub(replace, value)

    def walk(self, value: Any) -> Any:
        if isinstance(value, str):
            # Arguments and structured outputs often contain a second JSON layer.
            try:
                nested = json.loads(value)
            except (ValueError, TypeError):
                return self.text(value)
            if isinstance(nested, (dict, list)):
                return json.dumps(self.walk(nested), ensure_ascii=False)
            return self.text(value)
        if isinstance(value, dict):
            return {self.text(k): (self.text(v, code=True) if k == 'input' and isinstance(v, str)
                    and value.get('type') == 'custom_tool_call' and value.get('name') == 'exec'
                    else self.walk(v)) for k, v in value.items()}
        if isinstance(value, list):
            return [self.walk(v) for v in value]
        return value


def extract(path: Path, redactor: Redactor) -> tuple[list[dict[str, Any]], int]:
    """Keep every command lifecycle and code call/output, in source order."""
    events: list[dict[str, Any]] = []
    calls: set[str] = set()
    dropped = 0
    for line in path.read_text().splitlines():
        if redactor.forbidden_line(line):
            dropped += 1
            continue
        event = json.loads(line)
        kind = event.get('type')
        item = event.get('payload' if kind in {'response_item', 'event_msg'} else 'item', {})
        if kind == 'event_msg':
            item = item.get('item', {})
        if not isinstance(item, dict):
            continue
        tool_type = item.get('type')
        call = tool_type in {'custom_tool_call', 'function_call'}
        if call:
            calls.add(item.get('call_id', ''))
        output = tool_type in {'custom_tool_call_output', 'function_call_output'}
        command = (tool_type in {'command_execution', 'CommandExecution'} or
                   (str(kind).startswith('item.') and ('command' in item or 'arguments' in item)))
        if not (call or command or (output and item.get('call_id', '') in calls)):
            continue
        event = redactor.walk(event)
        # Keep short structured displays intact. Long outputs have a total
        # 2000-character budget, including their serialized envelope.
        def truncate(value: Any) -> Any:
            if isinstance(value, str):
                return value[:2000]
            serialized = json.dumps(value, ensure_ascii=False)
            return serialized[:2000] if len(serialized) > 2000 else value
        target = event.get('payload' if kind in {'response_item', 'event_msg'} else 'item', {})
        if kind == 'event_msg':
            target = target.get('item', {})
        for key in ('output', 'aggregated_output'):
            if key in target:
                target[key] = truncate(target[key])
        events.append(event)
    return events, dropped


def assert_safe(record: Any, markers: tuple[str, ...] | None = None) -> None:
    """Reject leaked markers and all literal absolute paths in fixture values."""
    if markers is None:
        markers = forbidden_markers()
    guards = record.get('marker_guards', []) if isinstance(record, dict) else []
    def visit(value: Any, *, code: bool = False) -> None:
        if isinstance(value, str):
            text = decoded(value)
            folded = text.casefold()
            for guard in guards:
                size = guard['characters']
                if any(hashlib.sha256(folded[i:i + size].encode()).hexdigest() == guard['sha256']
                       for i in range(len(folded) - size + 1)):
                    raise ValueError('Unsafe corpus content')
            paths = [part for part, regex in code_parts(text) if not regex] if code else [text]
            if any(m.casefold() in text.casefold() for m in markers) or any(ABSOLUTE.search(p) for p in paths):
                raise ValueError('Unsafe corpus content')
        elif isinstance(value, dict):
            for k, v in value.items():
                visit(k)
                visit(v, code=k == 'input' and value.get('type') == 'custom_tool_call' and value.get('name') == 'exec')
        elif isinstance(value, list):
            for v in value:
                visit(v)
    visit(record)


def audit_record(record: dict[str, Any]) -> dict[str, Any]:
    """Audit a sanitized stream in an isolated synthetic directory topology."""
    assert_safe(record)
    with tempfile.TemporaryDirectory(prefix='corpus-replay-') as directory:
        root = Path(directory)
        workspace = root / 'runtime/workspace'
        workspace.mkdir(parents=True)
        repository = root / 'repository'
        repository.mkdir()
        private = root / 'trusted'
        private.mkdir()
        replacements = {'__WORKSPACE__': str(workspace), '__RUNTIME__': str(workspace.parent),
                        '__REPOSITORY__': str(repository), '__HOME__': str(Path.home()),
                        '__TEMP__': str(root / 'temp'), '__HOST_TEMP__': str(root / 'host-temp'),
                        '__USR__': '/usr', '__BIN__': '/bin', '__DEV__': '/dev'}
        def restore(value: Any) -> Any:
            if isinstance(value, str):
                for label, path in replacements.items():
                    value = value.replace(label, path)
                return re.sub(r'__PATH_(\d+)__', lambda m: str(root / 'other' / m[1]), value)
            if isinstance(value, dict):
                return {restore(k): restore(v) for k, v in value.items()}
            if isinstance(value, list):
                return [restore(v) for v in value]
            return value
        events = restore(record['events'])
        log = root / 'corpus.jsonl'
        # Synthetic framing supplies stream context only; tool lifecycle records
        # remain verbatim apart from location redaction/output truncation.
        rows = [{'type': 'session_meta', 'payload': {'id': 'corpus'}}] + events
        rows.append({'type': 'turn.completed'})
        log.write_bytes(b''.join(canonical(row) + b'\n' for row in rows))
        result = audit_logs([log], PrivateGraders(private, ()), workspace=workspace, repository=repository)
        return {'status': result['status'],
                'error_kinds': sorted({error.split(':', 1)[0] for error in result['errors']}),
                'markers': sorted({match['marker'] for match in result['matches']})}


def export_report(report: Path, *, home: Path, temp: Path, repository: Path,
                  private_roots: list[Path], markers: list[str]) -> list[dict[str, Any]]:
    """Follow the checkpoint; missing evidence is an error, never an empty export."""
    published = json.loads((report / 'report.json').read_text())
    checkpoint = json.loads((report / 'checkpoint.json').read_text())
    if {t['task_id'] for t in published['tasks']} != set(checkpoint['tasks']):
        raise ValueError('Report/checkpoint task mismatch')
    records = []
    for task, entry in sorted(checkpoint['tasks'].items()):
        runtime = Path(entry['runtime'])
        if not runtime.is_absolute() or not runtime.is_dir():
            raise ValueError('Retained runtime unavailable')
        paths = [runtime / segment['events'] for segment in entry['segments']]
        if any(path.parent != runtime for path in paths):
            raise ValueError('Invalid segment filename')
        paths += sorted((runtime / 'codex-home/sessions').rglob('*.jsonl'))
        if not paths:
            raise ValueError('Missing retained logs')
        for path in dict.fromkeys(paths):
            redactor = Redactor(home=home, temp=temp, repository=repository, runtime=runtime,
                                private_roots=private_roots, markers=markers)
            events, dropped = extract(path, redactor)
            source = str(path.relative_to(runtime))
            record = {'id': f'{report.name}:{task}:{hashlib.sha256(source.encode()).hexdigest()[:16]}',
                      'origin': 'retained', 'events': events, 'dropped_private_lines': dropped,
                      'marker_guards': [{'characters': len(m.casefold()),
                                         'sha256': hashlib.sha256(m.casefold().encode()).hexdigest()}
                                        for m in [*markers, str(home), str(temp), str(repository), str(runtime)] if m]}
            assert_safe(record, tuple(redactor.forbidden))
            record['content_sha256'] = content_hash(record)
            record['expected'] = audit_record(record)
            records.append(record)
    return records


def write_records(path: Path, records: list[dict[str, Any]], rebaseline: set[str]) -> list[dict[str, Any]]:
    """Refuse silent replacement; return explicit old/new review entries."""
    previous = {row['id']: row for row in map(json.loads, path.read_text().splitlines())} if path.exists() else {}
    current = {row['id']: row for row in records}
    if len(current) != len(records) or previous.keys() - current.keys():
        raise ValueError('Duplicate or removed corpus records require manual review')
    changes = []
    for record in records:
        old = previous.get(record['id'])
        if old != record:
            if old is not None and record['id'] not in rebaseline:
                raise BaselineChange('Changed corpus record requires --rebaseline ' + record['id'])
            changes.append({'id': record['id'], 'before': old, 'after': record})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b''.join(canonical(record) + b'\n' for record in records))
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reports-root', type=Path, default=Path('eval/reports'))
    parser.add_argument('--output', type=Path, default=Path('tests/eval/fixtures/corpus'))
    parser.add_argument('--report', action='append')
    parser.add_argument('--private-root', type=Path, action='append', required=True)
    parser.add_argument('--private-marker', action='append', required=True)
    parser.add_argument('--home', type=Path, default=Path.home())
    parser.add_argument('--temp-root', type=Path, default=Path(tempfile.gettempdir()))
    parser.add_argument('--repository', type=Path, default=Path.cwd())
    parser.add_argument('--rebaseline', action='append', default=[], metavar='RECORD_ID')
    args = parser.parse_args()
    try:
        names = args.report or [*REPORTS, *(p.name for p in sorted(args.reports_root.glob('pilot*')) if p.is_dir())]
        prepared = []
        for name in names:
            if not re.fullmatch(r'[a-zA-Z0-9_-]+', name):
                raise ValueError('Invalid report name')
            records = export_report(args.reports_root / name, home=args.home, temp=args.temp_root,
                                    repository=args.repository, private_roots=args.private_root,
                                    markers=args.private_marker)
            prepared.append((args.output / (name + '.jsonl'), records))
        for path, records in prepared:
            for change in write_records(path, records, set(args.rebaseline)):
                # Full sanitized before/after is intentional review evidence.
                print(json.dumps(change, sort_keys=True))
    except BaselineChange as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError):
        print('Corpus export failed: unavailable/invalid evidence or unapproved baseline change', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
