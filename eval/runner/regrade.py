"""Re-audit and regrade every task of a finished, hash-pinned retained run."""

import argparse
from collections import Counter
import copy
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Callable
import uuid

from eval.metrics import compute, total
from eval.runner import core
from eval.runner.audit import FingerprintCache, PrivateGraders, audit_retained_logs, interrupted_logs, digest
from eval.runner.process import ProcessResult, run_process
from eval.runner.signals import stop_signals
from eval.runner.reaudit import InputParser
from eval.runner.report import build_task, validate


def audit_code_version() -> dict[str, str]:
    """Pin the audit implementation, including uncommitted parser changes."""
    directory = Path(__file__).parent
    return {name: digest((directory / name).read_bytes()) for name in ('audit.py', 'javascript.py', 'regrade.py')}


def regrade(private_root: Path, source: Path, out: Path, *,
            execute: Callable[..., ProcessResult] = run_process,
            _fresh_tasks: frozenset[str] = frozenset()) -> Path:
    """Reuse executor evidence and accounting; execute only the trusted grade() path."""
    source, out = source.resolve(), out.resolve()
    if out.exists() or out.is_relative_to(source) or source.is_relative_to(out):
        raise ValueError("Regrade requires a fresh output directory separate from the source run")
    source_bytes = (source / 'report.json').read_bytes()
    original = json.loads(source_bytes)
    state = json.loads((source / 'checkpoint.json').read_text())
    entries = state.get('tasks')
    config = state.get('config')
    if (state.get('report_schema') != 'evaluation-report-v1' or not isinstance(entries, dict) or
            not entries or set(entries) != {task['task_id'] for task in original['tasks']} or
            any(not re.fullmatch(r'[a-z0-9][a-z0-9-]*', task) for task in entries) or
            any(e.get('phase') != 'finished' or e.get('pid') for e in entries.values())):
        raise ValueError("Regrade requires a complete finished version-1 run")
    # Never reconstruct an exit hash from today's workspace for a historical run.
    if not _fresh_tasks <= set(entries):
        raise ValueError("Regrade refused: unknown fresh task")
    if any(not re.fullmatch(r'[0-9a-f]{64}', e.get('workspace_exit_sha256', ''))
           for task, e in entries.items() if task not in _fresh_tasks):
        raise ValueError("Regrade refused: runner-recorded workspace exit hash missing; rerun the executor on the host")
    if not isinstance(config, dict) or set(config.get('tasks', [])) != set(entries):
        raise ValueError("Regrade requires the runner-recorded configuration")
    validate(original, core.REPOSITORY)
    metadata = original['metadata']
    config_metadata = {'name': 'config_name', 'model': 'executor_model', 'reasoning_effort': 'reasoning_effort',
                       'control_backend': 'control_backend', 'seed': 'seed', 'reinstruction_limit': 'reinstruction_limit',
                       'codex_version': 'codex_version'}
    if (any(state.get(key) != metadata[key] for key in ('run_id', 'config_sha256', 'task_set_sha256')) or
            any(config.get(key) != metadata[field] for key, field in config_metadata.items())):
        raise ValueError("Regrade refused: source report and checkpoint provenance differ")
    private_by_task = {task: PrivateGraders.load(private_root, task, core.REPOSITORY, task_root=config.get("task_root")) for task in entries}
    population = dict(private_by_task)
    for task in config.get('task_population', []):
        if task not in population:
            population[task] = PrivateGraders.load(private_root, task, core.REPOSITORY, task_root=config.get("task_root"))
    if (core.configured_digest(population, config) != state['task_set_sha256'] or
            core.configured_digest(private_by_task, config) != state.get('selected_task_set_sha256', state['task_set_sha256'])):
        raise ValueError("Regrade refused: public/private task inputs differ from the source run")
    if out.is_relative_to(private_root.resolve()) or private_root.resolve().is_relative_to(out):
        raise ValueError("Regrade output must be separate from private grader storage")
    checks = []
    old_by_id = {t['task_id']: t for t in original['tasks']}
    for task, entry in entries.items():
        runtime = Path(entry['runtime'])
        if (not runtime.is_absolute() or out.is_relative_to(runtime.resolve()) or
                runtime.resolve().is_relative_to(out) or (not entry['segments'] and task not in _fresh_tasks) or any(
                    Path(s['events']).name != s['events'] for s in entry['segments'])):
            raise ValueError("Invalid retained runtime manifest or output location")
        if task in _fresh_tasks:
            continue  # Fresh reruns never reuse the source workspace or grading.
        if old_by_id[task]['two_session'] and not (
                old_by_id[task]['outcome'] == 'invalid' and not entry.get('day2_observation') and
                not any(s.get('day') == 2 for s in entry['segments'])):
            if not core.valid_day2_observation(entry, core.task_directory(config) / task):
                raise ValueError("Regrade refused: two-session exit hashes or day-2 observation missing")
        observed = core.workspace_digest(runtime / 'workspace')
        expected = entry['workspace_exit_sha256']
        if observed != expected:
            raise ValueError(f"Regrade refused: workspace exit hash mismatch for {task}")
        checks.append({'task_id': task, 'expected_sha256': expected, 'observed_sha256': observed, 'matched': True})
    # All task hashes are checked before any destination or grading copy is made.
    out.mkdir(parents=True)
    cache = FingerprintCache()
    report = copy.deepcopy(original)
    report['metadata'].update(run_id=uuid.uuid4().hex, created_at=core.now())
    tasks = []
    new_state = copy.deepcopy(state)
    new_state.update(run_id=report['metadata']['run_id'], created_at=report['metadata']['created_at'])
    for old_task in original['tasks']:
        task = old_task['task_id']
        entry, private = entries[task], private_by_task[task]
        if task in _fresh_tasks:
            (out / task).mkdir()
            tasks.append(copy.deepcopy(old_task))
            continue
        runtime = Path(entry['runtime'])
        workspace = runtime / 'workspace'
        paths = [runtime / segment['events'] for segment in entry['segments']]
        paths.extend(sorted((runtime / 'codex-home/sessions').rglob('*.jsonl')))
        audit = audit_retained_logs(paths, private, interrupted_paths=interrupted_logs(runtime, entry["segments"]), retained_context=entry.get("retained_audit_context"), workspace=workspace, repository=core.REPOSITORY,
                           grading_roots=core.audit_roots(runtime), fingerprint_cache=cache)
        previous = entry['result']['grader_access_audit']
        manifest = lambda logs: Counter((log['name'], log['sha256'], log['bytes']) for log in logs)
        if not previous['logs'] or manifest(previous['logs']) != manifest(audit['logs']):
            audit['errors'].append('retained_log_manifest_mismatch')
        if (previous['root_fingerprint'] != audit['root_fingerprint'] or
                previous['grader_fingerprints'] != audit['grader_fingerprints']):
            audit['errors'].append('private_grader_manifest_mismatch')
        if audit['errors'] and audit['status'] == 'clean':
            audit['status'] = 'inconclusive'
        result = copy.deepcopy(entry['result'])
        result['grader_access_audit'] = audit
        result['invalid_reasons'] = [reason for reason in result['invalid_reasons']
                                     if reason not in {'incomplete_access_audit', 'grader_access_detected'}]
        if audit['status'] != 'clean':
            result['invalid_reasons'].append('grader_access_detected' if audit['status'] == 'access_detected'
                                             else 'incomplete_access_audit')
        task_out = out / task
        task_out.mkdir()
        # Copy published evidence only; never follow source symlinks or copy old
        # grading copies/workspaces into an executor-accessible location.
        for path in (source / task).iterdir():
            if path.is_file() and not path.is_symlink() and path.name not in {
                    'result.json', 'access-audit.json', 'grading.log'}:
                core.publish(path, task_out / path.name, private)
        core.write_json(task_out / 'access-audit.json', json.loads(private.redact(json.dumps(audit))))
        result['grading'] = None
        last = entry['segments'][-1]
        if (audit['status'] == 'clean' and not result['invalid_reasons'] and
                last['exit_code'] == 0 and not last.get('timed_out') and
                old_task['outcome'] not in {'timeout', 'error'}):
            if core.workspace_digest(workspace) != entry['workspace_exit_sha256']:
                raise ValueError(f"Regrade refused: workspace exit hash mismatch for {task}")
            scratch = Path(tempfile.mkdtemp(prefix='lhm-eval-regrade-'))
            result['grading'] = core.grade(
                workspace, private, scratch, task_out / 'grading.log',
                json.loads((core.task_directory(config) / task / 'expected.json').read_text()),
                config['grading_timeout_seconds'], execute)
            if core.workspace_digest(workspace) != entry['workspace_exit_sha256']:
                raise ValueError(f"Regrade refused: workspace changed during grading for {task}")
        result['outcome'] = ('invalid' if result['invalid_reasons'] else
                             old_task['outcome'] if old_task['outcome'] in {'timeout', 'error'} else
                             'timeout' if last.get('timed_out') else 'error' if last['exit_code'] != 0 else
                             result['grading']['result'] if result['grading'] else 'error')
        sanitized = json.loads(private.redact(json.dumps(result)))
        core.write_json(task_out / 'result.json', sanitized)
        new_state['tasks'][task]['result'] = sanitized
        shared = build_task(result, entry, task_out, config, original['metadata']['pricing'], old_task)
        # Regrading does not change executor/control accounting or observations.
        for key in ('calls', 'costs', 'done_claims'):
            shared[key] = copy.deepcopy(old_task[key])
        tasks.append(shared)
    report['tasks'] = tasks
    report['metrics'] = compute(tasks, seed=original['metadata']['confidence']['seed'],
                                resamples=original['metadata']['confidence']['resamples'])
    # The runner still has no complete done-claim denominator.
    if all(task['done_claims']['claimed_items'] == 0 for task in tasks):
        report['metrics']['false_done_rate'] = copy.deepcopy(original['metrics']['false_done_rate'])
    report['accounting'] = {'attempted_tasks': len(tasks), 'valid_tasks': sum(t['outcome'] != 'invalid' for t in tasks),
                            'invalid_tasks': sum(t['outcome'] == 'invalid' for t in tasks),
                            'total_cost_usd': total([t['costs']['total_usd'] for t in tasks])}
    reasons = [f"{t['task_id']}: {reason}" for t in tasks for reason in t['invalid_reasons']]
    report['validity'] = {'status': 'invalid' if reasons else 'valid', 'reasons': reasons}
    validate(report, core.REPOSITORY)
    core.write_json(out / 'checkpoint.json', new_state)
    core.write_json(out / 'run-diagnostics.json', {
        'task_root': config.get('task_root', 'eval/tasks'), 'service_tier': config.get('service_tier'),
        'source': str(source), 'source_report_sha256': digest(source_bytes),
        'audit_code_version': audit_code_version(), 'workspace_hash_checks': checks})
    text = json.dumps(report, indent=2) + '\n'
    for private in private_by_task.values():
        text = private.redact(text)
    (out / 'report.json').write_text(core.checkout_text(text))
    return out / 'report.json'


def main() -> int:
    """Print the new output directory only on success; errors never expose private paths."""
    parser: argparse.ArgumentParser = InputParser(description=__doc__)
    parser.add_argument('--private-root', type=Path, required=True)
    parser.add_argument('--from', dest='source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    try:
        args = parser.parse_args()
        with stop_signals(args.out):
            regrade(args.private_root, args.source, args.out)
    except KeyboardInterrupt:
        print('Regrade interrupted; stop diagnostics retained', file=sys.stderr)
        return 130
    except FileNotFoundError:
        print('Regrade input error: retained evidence unavailable', file=sys.stderr)
        return 1
    except ValueError as exc:
        # Only our explicit public diagnostics are safe to display.
        message = str(exc) if str(exc).startswith('Regrade ') else 'Regrade input error: finished evidence unavailable or invalid'
        print(message, file=sys.stderr)
        return 1
    except Exception:
        print('Regrade internal error', file=sys.stderr)
        return 2
    print(str(args.out))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
