"""Prove narrow name-only enumerations from paired, complete tool records."""

import json
from pathlib import Path
import re
import shlex
from typing import Any, Callable


def listing_spec(command: str) -> tuple[list[str], set[str]] | None:
    """Accept a single rg --files or side-effect-free find expression only."""
    if len(command) > 32768 or any(char in command for char in '\n\r$`'):
        return None
    try:
        words = shlex.split(command)
    except ValueError:
        return None
    if len(words) > 256 or words.count('(') > 32:
        return None
    if words[-1:] == ['2>/dev/null']:
        words.pop()
    if not words or words[0] not in {'rg', 'find'}:
        return None
    roots: list[str] = []
    names: set[str] = set()

    def positive(pattern: str) -> bool:
        if (not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]*', pattern) or
                pattern.lower().endswith('.py') or
                re.search(r'hidden|grader|reference|^test[_.-]', pattern, re.I)):
            raise ValueError('unsafe_name')
        names.add(pattern)
        return True

    try:
        if words[0] == 'rg':
            if '--files' not in words:
                return None
            index = 1
            while index < len(words):
                word = words[index]
                index += 1
                if word in {'--files', '--hidden'}:
                    continue
                if word in {'-g', '--glob'}:
                    pattern = words[index]
                    index += 1
                    if not pattern.startswith('!'):
                        positive(pattern)
                elif word.startswith('--glob='):
                    pattern = word.split('=', 1)[1]
                    if not pattern.startswith('!'):
                        positive(pattern)
                elif re.fullmatch(r'[/A-Za-z0-9_.-]+', word) and not word.startswith('-'):
                    roots.append(word)
                else:
                    return None
        else:
            if words[-1:] == ['-print']:
                words.pop()
            index = 1
            while index < len(words) and not words[index].startswith('-') and words[index] not in {'!', '('}:
                root = words[index]
                if not re.fullmatch(r'[/A-Za-z0-9_.-]+', root):
                    return None
                roots.append(root)
                index += 1

            def atom() -> bool:
                nonlocal index
                word = words[index]
                index += 1
                if word == '(':
                    restricted = expression()
                    if words[index] != ')':
                        raise ValueError('parenthesis')
                    index += 1
                    return restricted
                excluded = word in {'!', '-not'}
                if excluded:
                    word = words[index]
                    index += 1
                if word in {'-name', '-path'}:
                    pattern = words[index]
                    index += 1
                    if excluded:
                        return False
                    if word != '-name':
                        raise ValueError('positive_path')
                    return positive(pattern)
                if not excluded and word == '-type' and words[index] == 'f':
                    index += 1
                    return False
                raise ValueError('unsupported_find')

            def conjunction() -> bool:
                nonlocal index
                restricted = atom()
                while index < len(words) and words[index] not in {'-o', '-or', ')'}:
                    if words[index] in {'-a', '-and'}:
                        index += 1
                    # Do not short-circuit: every operand must be validated.
                    other = atom()
                    restricted = restricted or other
                return restricted

            def expression() -> bool:
                nonlocal index
                restricted = conjunction()
                while index < len(words) and words[index] in {'-o', '-or'}:
                    index += 1
                    other = conjunction()
                    restricted = restricted and other
                return restricted

            if not expression() or index != len(words):
                return None
    except (IndexError, ValueError):
        return None
    return (roots or ['.'], names) if names else None


class ListingEvidence:
    """Associate a command with its own completion, never another invocation."""

    def __init__(self, data: bytes, unwrap: Callable[[str], str]) -> None:
        self.unwrap = unwrap
        self.rows: dict[int, dict[str, Any]] = {}
        self.completions: list[tuple[int, dict[str, Any]]] = []
        for number, line in enumerate(data.decode('utf-8', errors='replace').splitlines(), 1):
            try:
                event = json.loads(line)
                if not isinstance(event, dict):
                    continue
            except ValueError:
                continue
            self.rows[number] = event
            if event.get('type') == 'item.completed':
                item = event.get('item', {})
            elif event.get('type') == 'event_msg' and isinstance(event.get('payload'), dict) and event['payload'].get('type') == 'item_completed':
                item = event['payload'].get('item', {})
            else:
                continue
            if isinstance(item, dict) and item.get('type') in {'command_execution', 'CommandExecution'}:
                self.completions.append((number, item))

    def key(self, command: Any) -> tuple[str, ...] | None:
        try:
            if isinstance(command, list) and all(isinstance(word, str) for word in command):
                command = shlex.join(command)
            return tuple(shlex.split(self.unwrap(command))) if isinstance(command, str) else None
        except ValueError:
            return None

    def paired(self, number: int, command: str) -> tuple[int, dict[str, Any]] | None:
        event = self.rows.get(number, {})
        kind = event.get('type')
        payload = event.get('payload', {})
        item = event.get('item', {}) if kind != 'response_item' else payload
        candidates = []
        if kind == 'event_msg' or kind == 'item.completed':
            candidates = [(line, item) for line, item in self.completions if line == number]
        elif kind in {'item.started', 'item.updated'}:
            end = min((line for line, row in self.rows.items() if line > number and
                       row.get('type') in {'session_meta', 'thread.started'}), default=len(self.rows) + 1)
            candidates = [(line, completed) for line, completed in self.completions
                          if number < line < end and completed.get('id') == item.get('id') and item.get('id')]
        elif kind == 'response_item' and item.get('type') in {'custom_tool_call', 'function_call'}:
            end = min((line for line, row in self.rows.items() if line > number and (
                row.get('type') in {'session_meta', 'thread.started'} or
                row.get('type') == 'response_item' and isinstance(row.get('payload'), dict) and (
                    row['payload'].get('type') in {'custom_tool_call', 'function_call'} or
                    row['payload'].get('call_id') == item.get('call_id')))), default=len(self.rows) + 1)
            candidates = [(line, completed) for line, completed in self.completions if number < line < end]
        candidates = [(line, completed) for line, completed in candidates
                      if self.key(completed.get('command')) == self.key(command)]
        return candidates[0] if len(candidates) == 1 else None

    def prove(self, number: int, command: str, cwd: Path | None, *,
              protected: Callable[[Path, bool], bool], workspace: Path | None,
              forbidden_names: set[str]) -> int | None:
        try:
            spec = listing_spec(self.unwrap(command))
        except ValueError:
            return None
        if spec is None or cwd is None:
            return None
        directories, names = spec
        if any(name.casefold() in forbidden_names for name in names):
            return None
        for value in directories:
            directory = Path(value)
            directory = directory if directory.is_absolute() else cwd / directory
            # Only traversal of an ancestor qualifies; directly named protected
            # roots/children and any second protected operand retain detection.
            if protected(directory, False):
                return None
        paired = self.paired(number, command)
        if paired is None:
            return None
        line, item = paired
        output = item.get('aggregated_output')
        if (item.get('status') not in {'completed', 'failed'} or type(item.get('exit_code')) is not int or
                not isinstance(output, str) or output and not output.endswith('\n') or
                re.search(r'truncat|omitted|\.\.\.|\x00|\x1b|\r', output, re.I) or
                any(item.get(key) for key in ('truncated', 'output_truncated', 'is_truncated'))):
            return None
        item_cwd = item.get('cwd', item.get('workdir'))
        if isinstance(item_cwd, str) and Path(item_cwd.removeprefix('file://')).resolve() != cwd.resolve():
            return None
        for value in output.splitlines():
            candidate = Path(value)
            candidate = candidate if candidate.is_absolute() else cwd / candidate
            if (not value or any(ord(char) < 32 for char in value) or candidate.name not in names or
                    protected(candidate, False) or any(part.casefold().startswith('lhm-eval-') for part in candidate.resolve().parts) or
                    workspace is not None and candidate.resolve().is_relative_to(workspace.parent.resolve())):
                return None
        return line
