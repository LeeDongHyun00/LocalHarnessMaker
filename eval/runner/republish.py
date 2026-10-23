"""Restore hash-pinned, redacted evidence of an already finished evaluation."""

import argparse
from collections import Counter
import copy
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

from jsonschema import ValidationError

from eval.runner import core
from eval.runner.audit import PrivateGraders, digest
from eval.runner.publication import checkout_text, control_target, evidence_path, review_bytes, safe_source
from eval.runner.reaudit import InputParser
from eval.runner.schema_compat import validate_schema


def relative_name(name: str) -> Path:
    """Accept only normalized relative evidence names outside the workspace."""
    path = Path(name)
    if (not name or path.is_absolute() or '..' in path.parts or str(path) != name or
            'workspace' in path.parts or path == Path('.')):
        raise ValueError('Unsafe evidence name')
    return path


def read_pinned(path: Path, root: Path, expected: str) -> bytes:
    """Read regular evidence with a recorded SHA-256, never through runtime links."""
    if (not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected) or
            not safe_source(path, root) or not path.is_file()):
        raise ValueError('Missing or unsafe pinned evidence')
    data = path.read_bytes()
    if digest(data) != expected:
        raise ValueError('Pinned evidence hash mismatch')
    return data


def republish(private_root: Path, out: Path, runtime_root: Path | None = None, *,
              allow_unpinned: bool = False) -> list[dict[str, Any]]:
    """Preflight every task before writing; change only report artifact entries.

    Old stderr/final captures are skipped unless explicitly allowed and labeled.
    No model, grader, subprocess, workspace copy or checkpoint rewrite is performed.
    """
    # Do not resolve runtime roots: links at the boundary itself must remain visible.
    out = Path(os.path.abspath(out))
    if any(not safe_source(out / name, out) or not (out / name).is_file()
           for name in ('checkpoint.json', 'report.json')):
        raise ValueError('Finished run manifests are unavailable')
    state = json.loads((out / 'checkpoint.json').read_text())
    original = json.loads((out / 'report.json').read_text())
    validate_schema(original, core.REPOSITORY)
    entries = state.get('tasks')
    tasks = original['tasks']
    if (state.get('report_schema') not in {'evaluation-report-v1', 'evaluation-report-v2'} or
            not isinstance(entries, dict) or not entries or
            len(tasks) != len(entries) or {t['task_id'] for t in tasks} != set(entries) or
            any(not re.fullmatch(r'[a-z0-9][a-z0-9-]*', task) for task in entries) or
            set(state.get('config', {}).get('tasks', [])) != set(entries) or
            any(e.get('phase') != 'finished' or e.get('pid') for e in entries.values()) or
            any(state.get(k) != original['metadata'][k]
                for k in ('run_id', 'config_sha256', 'task_set_sha256'))):
        raise ValueError('A complete finished run with matching provenance is required')
    if (out.resolve().is_relative_to(private_root.resolve()) or
            private_root.resolve().is_relative_to(out.resolve())):
        raise ValueError('Output overlaps private storage')
    report = copy.deepcopy(original)
    diagnostics_path = out / 'run-diagnostics.json'
    diagnostics: dict[str, Any] = {}
    if allow_unpinned:
        if not safe_source(diagnostics_path, out):
            raise ValueError('Unsafe diagnostics destination')
        if diagnostics_path.exists():
            diagnostics = json.loads(diagnostics_path.read_text())
        if not isinstance(diagnostics, dict):
            raise ValueError('Invalid run diagnostics')
    original_diagnostics = copy.deepcopy(diagnostics)
    unpinned_records: dict[tuple[str, str], dict[str, str]] = {}
    if allow_unpinned:
        republication = diagnostics.get('republication', {})
        if not isinstance(republication, dict) or not isinstance(republication.get('artifacts', []), list):
            raise ValueError('Invalid republication diagnostics')
        for record in republication.get('artifacts', []):
            if (not isinstance(record, dict) or set(record) != {'task_id', 'path', 'sha256', 'provenance'} or
                    record['task_id'] not in entries or record['provenance'] != 'republished_unpinned'):
                raise ValueError('Invalid republication provenance')
            path = evidence_path(record['path'])
            if (path.parent != out / record['task_id'] or
                    not re.fullmatch(r'(?:exec-[0-9]+\.stderr|final-[0-9]+\.md)', path.name)):
                raise ValueError('Unsafe republication provenance')
            key = (record['task_id'], record['path'])
            if key in unpinned_records:
                raise ValueError('Duplicate republication provenance')
            unpinned_records[key] = record
    pending: dict[Path, bytes] = {}
    rows = []
    for task in report['tasks']:
        task_id = task['task_id']
        entry = entries[task_id]
        recorded = Path(entry['runtime'])
        runtime = (Path(os.path.abspath(runtime_root)) / task_id) if runtime_root is not None else recorded
        task_out = out / task_id
        if (not recorded.is_absolute() or '..' in recorded.parts or not runtime.is_absolute() or
                not safe_source(runtime, runtime) or not runtime.is_dir() or
                not safe_source(task_out, out) or not task_out.is_dir() or
                runtime.resolve().is_relative_to(core.REPOSITORY.resolve()) or
                runtime.resolve().is_relative_to(out.resolve()) or out.resolve().is_relative_to(runtime.resolve()) or
                runtime.resolve().is_relative_to(private_root.resolve()) or
                private_root.resolve().is_relative_to(runtime.resolve())):
            raise ValueError('Unsafe retained runtime or destination')
        private = PrivateGraders.load(private_root, task_id, core.REPOSITORY,
                                      task_root=state['config'].get('task_root'))
        segments = entry['segments']
        if entry['result'].get('segments') != segments:
            raise ValueError('Checkpoint segment manifests differ')
        published_segments = {s['attempt']: s for s in task['executor_segments']}
        if (len(published_segments) != len(task['executor_segments']) or
                not set(published_segments) <= {s['attempt'] for s in segments}):
            raise ValueError('Report segment manifests differ')
        # Pin all runner-created control files, including those deliberately not published.
        pinned: dict[str, str] = {}

        def pin(name: str, expected: str) -> None:
            relative_name(name)
            if name in pinned and pinned[name] != expected:
                raise ValueError('Conflicting evidence hashes')
            pinned[name] = expected

        for name, expected in entry.get('control_files', {}).items():
            pin(name, expected)
        candidates: dict[str, Path] = {}
        unpinned = 0
        native_names = set()
        for index, segment in enumerate(segments, 1):
            if (segment['attempt'] != index or 'exited_at' not in segment or
                    type(segment.get('exit_code')) is not int or
                    segment['events'] != f'exec-{index}.jsonl' or segment['stderr'] != f'exec-{index}.stderr'):
                raise ValueError('Invalid segment manifest')
            published = published_segments.get(index)
            if published:
                if any(segment[k] != published[k] for k in ('started_at', 'exited_at', 'exit_code')):
                    raise ValueError('Report segment metadata mismatch')
                if evidence_path(published['events']['path']) != recorded / segment['events']:
                    raise ValueError('Report segment source mismatch')
                pin(segment['events'], published['events']['sha256'])
            allowed = {segment['events'], segment['stderr'], f'final-{index}.md'}
            for name, expected in segment.get('evidence_sha256', {}).items():
                if name not in allowed:
                    raise ValueError('Unexpected segment evidence')
                pin(name, expected)
            for name in allowed:
                candidates[name] = task_out / name
            for value in segment.get('native_logs', []):
                path = Path(value)
                if not path.is_relative_to(recorded / 'codex-home/sessions'):
                    raise ValueError('Unsafe native segment path')
                native_names.add(str(relative_name(str(path.relative_to(recorded)))))
        sessions = runtime / 'codex-home/sessions'
        if not safe_source(sessions, runtime):
            raise ValueError('Unsafe native evidence root')
        native_names.update(str(p.relative_to(runtime)) for p in sessions.rglob('*.jsonl'))
        log_names = {s['events'] for s in segments} | native_names
        audit_logs = entry['result']['grader_access_audit']['logs']
        manifest = Counter((log['name'], log['sha256'], log['bytes']) for log in audit_logs)
        # Audit manifests identify native streams by basename. Reject ambiguity rather
        # than letting one matching basename authorize another file.
        if len({Path(name).name for name in log_names}) != len(log_names):
            raise ValueError('Ambiguous audit log names')
        expected_logs = {log['name']: log for log in audit_logs}
        if len(expected_logs) != len(audit_logs) or set(expected_logs) != {Path(n).name for n in log_names}:
            raise ValueError('Audit log manifest differs from segment streams')
        observed = []
        for name in sorted(log_names):
            log = expected_logs[Path(name).name]
            pin(name, log['sha256'])
            data = read_pinned(runtime / relative_name(name), runtime, log['sha256'])
            observed.append((Path(name).name, digest(data), len(data)))
        if Counter(observed) != manifest:
            raise ValueError('Audit log size or hash mismatch')
        for name in entry.get('control_files', {}):
            target = control_target(runtime / name, runtime, task_out)
            if target is not None:
                candidates[name] = target
        # Verify all pins, not only the publication allowlist. This also verifies
        # merged transcripts without ever copying a workspace or grading file.
        raw = {name: read_pinned(runtime / relative_name(name), runtime, expected)
               for name, expected in pinned.items()}
        refs = {a['path']: a for a in task['artifacts']}
        refs_by_path = {evidence_path(a['path']): a for a in task['artifacts']}
        if len(refs) != len(task['artifacts']) or len(refs_by_path) != len(refs):
            raise ValueError('Duplicate artifact references')
        written = existing = 0
        published_unpinned = 0
        destinations: set[Path] = set()
        for name, target in sorted(candidates.items()):
            unverified = name not in raw
            if name not in raw:
                # Historical runner versions did not pin stderr/final bytes.
                source = runtime / relative_name(name)
                if not allow_unpinned or not re.fullmatch(r'(?:exec-[0-9]+\.stderr|final-[0-9]+\.md)', name):
                    unpinned += 1
                    continue
                if not safe_source(source, runtime):
                    raise ValueError('Unsafe unpinned capture')
                if not source.exists():
                    unpinned += 1
                    continue
                if not source.is_file():
                    raise ValueError('Invalid unpinned capture')
                raw[name] = source.read_bytes()
            data = review_bytes(raw[name], private)
            if not safe_source(target, out) or target in destinations:
                raise ValueError('Unsafe publication destination')
            destinations.add(target)
            prior = refs_by_path.get(target)
            ref = {'path': prior['path'] if prior else checkout_text(str(target)), 'sha256': digest(data)}
            if prior is not None and prior['sha256'] != ref['sha256']:
                raise ValueError('Published artifact pin conflicts with retained evidence')
            if unverified:
                key = (task_id, ref['path'])
                record = {**ref, 'task_id': task_id, 'provenance': 'republished_unpinned'}
                if key in unpinned_records and unpinned_records[key] != record:
                    raise ValueError('Unpinned publication provenance changed')
                unpinned_records[key] = record
            if target.exists():
                if not target.is_file() or target.read_bytes() != data:
                    raise ValueError('Existing published bytes differ')
                existing += 1
            else:
                if target in pending and pending[target] != data:
                    raise ValueError('Colliding publication destinations')
                pending[target] = data
                written += 1
                published_unpinned += int(unverified)
            refs[ref['path']] = ref
        # Preserve historical external references (including raw native streams),
        # while verifying their backup counterpart when original runtimes moved.
        for ref in task['artifacts']:
            path = evidence_path(ref['path'])
            if path.is_relative_to(recorded):
                name = str(relative_name(str(path.relative_to(recorded))))
                read_pinned(runtime / name, runtime, ref['sha256'])
            elif path.is_relative_to(out):
                if path in pending:
                    if digest(pending[path]) != ref['sha256']:
                        raise ValueError('Published artifact pin mismatch')
                else:
                    read_pinned(path, out, ref['sha256'])
        task['artifacts'] = list(refs.values())
        row = {'task_id': task_id, 'published': written, 'existing': existing, 'unpinned': unpinned}
        if allow_unpinned:
            row['published_unpinned'] = published_unpinned
        rows.append(row)
    if allow_unpinned and unpinned_records:
        # The frozen report artifact shape accepts path/sha256 only. Store the
        # richer artifact entries in diagnostics, never weaken schema validation.
        diagnostics.setdefault('republication', {})['artifacts'] = list(unpinned_records.values())
        for record in unpinned_records.values():
            path = evidence_path(record['path'])
            if path in pending:
                if digest(pending[path]) != record['sha256']:
                    raise ValueError('Unpinned artifact hash mismatch')
            else:
                read_pinned(path, out, record['sha256'])
    if diagnostics != original_diagnostics:
        diagnostics_hash = digest((json.dumps(diagnostics, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))
        for task in report['tasks']:
            for ref in task['artifacts']:
                if evidence_path(ref['path']) == diagnostics_path:
                    ref['sha256'] = diagnostics_hash
    validate_schema(report, core.REPOSITORY)
    # No output changes occur until all sources, destinations and report edits pass.
    # Exclusive creation also refuses a destination that appears after preflight.
    for target, data in pending.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        if not safe_source(target, out):
            raise ValueError('Unsafe publication destination')
        with target.open('xb') as stream:
            stream.write(data)
    for path, value, previous in ((diagnostics_path, diagnostics, original_diagnostics),
                                  (out / 'report.json', report, original)):
        if value == previous:
            continue
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=out,
                                         prefix='.republish-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
        temporary.replace(path)
    return rows


def main() -> int:
    """Print only counts and task IDs; never leak locations or source on failure."""
    parser: argparse.ArgumentParser = InputParser(description=__doc__)
    parser.add_argument('--private-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--runtime-root', type=Path)
    parser.add_argument('--allow-unpinned', action='store_true',
                        help='Restore unpinned executor stderr/finals and label their provenance in diagnostics')
    try:
        args = parser.parse_args()
        rows = republish(args.private_root, args.out, args.runtime_root, allow_unpinned=args.allow_unpinned)
    except (ValueError, OSError, KeyError, TypeError, ValidationError):
        print('Republication input error', file=sys.stderr)
        return 1
    except Exception:
        print('Republication internal error', file=sys.stderr)
        return 2
    for row in rows:
        print(json.dumps(row, sort_keys=True))
    keys = ('published', 'existing', 'unpinned') + (('published_unpinned',) if args.allow_unpinned else ())
    print(json.dumps({'tasks': len(rows), **{key: sum(r[key] for r in rows) for key in keys}}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
