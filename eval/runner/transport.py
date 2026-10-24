"""Classify terminal executor transport failures from retained structured events."""

import json
from pathlib import Path
import re
from typing import Any, Callable

from eval.runner.audit import digest
from eval.runner.telemetry import _instant, records, session_id


REASON = 'executor_transport_failure'
_TRANSPORT = re.compile(
    r'Reconnecting\.\.\.|stream disconnected before completion|'
    r'workspace routing discovery|No route to host|request timed out|'
    r'Connection failed|Transport error|failed to lookup address information|waiting for network|'
    r'Falling back from WebSockets to HTTPS transport', re.I)


def _message(event: dict[str, Any]) -> str | None:
    error = event.get('error')
    value = error.get('message') if isinstance(error, dict) else event.get('message')
    return value if isinstance(value, str) else None


def _same(left: str, right: str) -> bool:
    """The terminal error may omit the reconnect counter/wrapper."""
    def normalize(value: str) -> str:
        value = re.sub(r'^Reconnecting\.\.\.\s*[^\r\n(]*\((.*)\)\s*$', r'\1', value, flags=re.I)
        return value.strip().casefold()
    return normalize(left) == normalize(right)


def classify(segment: dict[str, Any], runtime: Path,
             redact: Callable[[str], str]) -> dict[str, Any] | None:
    """Require a terminal transport suffix, never stderr or assistant/tool prose.

    Each exec stream is process-specific. Native rollouts shared by resumes
    additionally require timestamps within this process's lifetime. Malformed
    or unsupported suffixes cannot establish a transport-only termination.
    Access auditing remains independent and is never waived by classification.
    """
    deadline_kill = bool(segment.get('timed_out')) and segment.get('exit_code') in (-9, None)
    if ((type(segment.get('exit_code')) is not int and not (
            deadline_kill and segment.get('exit_code') is None)) or type(segment.get('attempt')) is not int or
            not isinstance(segment.get('events'), str)):
        return None
    if (segment.get('interrupted') or segment.get('exit_code') == -2 or
            segment.get('exit_code') == 0 and not segment.get('timed_out')):
        return None
    events_path = runtime / segment['events']
    native = [Path(p) for p in segment.get('native_logs', [])]
    for path in dict.fromkeys([events_path, *native]):
        if not path.is_file():
            continue
        if path != events_path:
            sid = session_id([events_path])
            if sid is None or not any(e.get('type') == 'session_meta' and
                    isinstance(e.get('payload'), dict) and e['payload'].get('id') == sid for e in records(path)):
                continue  # Child rollouts cannot classify the parent executor.
        suffix: list[dict[str, Any]] = []
        failed = False
        completed = False
        valid = True
        deadline_only = True
        for number, line in enumerate(path.read_text(errors='replace').split('\n'), 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except ValueError:
                valid = False
                break
            if not isinstance(event, dict):
                valid = False
                break
            if path != events_path:
                start, end = _instant(segment.get('started_at')), _instant(segment.get('exited_at'))
                when = _instant(event.get('timestamp'))
                if start is None or end is None or when is None or not start <= when <= end:
                    continue
            if event.get('type') == 'event_msg' and isinstance(event.get('payload'), dict):
                event = event['payload']
            kind = event.get('type')
            if kind in {'turn.started', 'task_started'}:
                suffix, failed, completed = [], False, False
                deadline_only = True
                continue
            if kind in {'turn.completed', 'task_complete'}:
                suffix, completed = [], True
                continue
            item = event.get('item')
            if kind in {'item.completed', 'item_completed'} and isinstance(item, dict) and item.get('type') == 'error':
                message = _message(item)
            elif kind in {'error', 'turn.failed'}:
                message = _message(event)
            elif kind in {'thread.started', 'session_meta', 'turn_context', 'token_count', 'thread_settings_applied'}:
                deadline_only = False
                continue
            else:
                # A deadline needs an uninterrupted error-only suffix after
                # completed work. Starting another item cannot be hidden by
                # transport errors that arrive while that item is unfinished.
                deadline_only = kind in {'item.completed', 'item_completed'} and isinstance(item, dict)
                suffix, failed = [], False
                continue
            if not isinstance(message, str) or not _TRANSPORT.search(message):
                suffix, failed = [], False
                if kind in {'error', 'turn.failed'} or isinstance(item, dict) and item.get('type') == 'error':
                    completed = True  # A model-side terminal error cannot become transport-only.
                continue
            if completed or failed:
                suffix = []
                continue
            if kind == 'turn.failed':
                failed = bool(suffix) and any(_same(message, row['_raw']) for row in suffix)
                if not failed:
                    completed = True
                    suffix = []
                    continue
            suffix.append({'log': path.name, 'line': number, 'message': redact(message),
                           'evidence_sha256': digest(line.encode()), '_raw': message})
        if path == events_path and (not valid or completed or deadline_kill and not deadline_only):
            return None  # A native rollout cannot override explicit executor completion/model failure.
        if valid and suffix and (failed or deadline_kill) and not completed and (not deadline_kill or deadline_only):
            return {'attempt': segment['attempt'], 'day': segment.get('day', 1), 'reason': REASON,
                    'exit_code': segment['exit_code'], 'timed_out': bool(segment.get('timed_out')),
                    'log_sha256': digest(path.read_bytes()),
                    'errors': [{k: v for k, v in row.items() if k != '_raw'} for row in suffix]}
    return None


def inspect(entry: dict[str, Any], redact: Callable[[str], str]) -> list[dict[str, Any]]:
    """Classify every process; a later successful resume resolves its failure."""
    segments = entry.get('segments', [])
    last_by_day = {s.get('day', 1): s.get('attempt') for s in segments}
    failures = []
    for segment in segments:
        evidence = classify(segment, Path(entry['runtime']), redact)
        if evidence:
            evidence['resolved_by_resume'] = segment['attempt'] != last_by_day[segment.get('day', 1)]
            failures.append(evidence)
    return failures


def unresolved(failures: list[dict[str, Any]]) -> bool:
    return any(not row['resolved_by_resume'] for row in failures)


def summary(entries: dict[str, Any]) -> list[dict[str, Any]]:
    """Use already redacted result diagnostics for report-wide disclosure."""
    rows = []
    for task, entry in entries.items():
        rows.extend({'task_id': task, **failure} for failure in
                    entry.get('result', {}).get('diagnostics', {}).get('executor_transport_failures', []))
        history = entry.get('rerun_history', {})
        rows.extend({'task_id': task, **failure, 'rerun': {
            'rerun_id': history['rerun_id'], 'source_run_id': history['source_run_id'],
            'fresh_runtime': entry['runtime'], 'outcome': entry.get('result', {}).get('outcome')}}
            for failure in history.get('executor_transport_failures', []))
    return rows
