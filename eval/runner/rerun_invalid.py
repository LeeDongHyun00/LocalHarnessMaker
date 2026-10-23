"""Fresh reruns of infrastructure-invalid tasks, retaining all other evidence."""

import argparse
from collections import Counter
import copy
import json
from pathlib import Path
import sys
from typing import Any, Callable
import uuid

from eval.runner.pricing import extends, report_pricing
from eval.metrics import compute, total
from eval.runner import core, harness, regrade
from eval.runner.audit import PrivateGraders, audit_retained_logs, digest, interrupted_logs
from eval.runner.process import ProcessResult, run_process
from eval.runner.control_accounting import control_calls
from eval.runner.reaudit import InputParser
from eval.runner.report import artifact, validate
from eval.runner.signals import stop_signals


REASONS = frozenset({
    'control_cli_error', 'runner_control_file_preexisting', 'execution_interrupted',
    'incomplete_access_audit', 'missing_executor_session_id', 'executor_settings_unverified',
    'missing_cli_version_evidence', 'missing_two_session_handoff_observation',
    'executor_service_tier_missing_or_different', 'capacity_exhausted',
})


def eligible(task: dict[str, Any], entry: dict[str, Any], audit: dict[str, Any]) -> bool:
    """Whitelist causes, not quality outcomes; unexplained audit errors stay invalid."""
    result = entry.get('result', {})
    reasons = set(task.get('invalid_reasons', []))
    historical = result.get('grader_access_audit', {})
    if (task.get('outcome') != 'invalid' or result.get('outcome') != 'invalid' or
            not reasons or not reasons <= REASONS or
            not set(result.get('invalid_reasons', [])) <= reasons or
            any(a.get('matches') or a.get('status') == 'access_detected'
                for a in (task.get('grader_access_audit', {}), historical, audit))):
        return False
    segments = entry.get('segments', [])
    interrupted = [s for s in segments if s.get('exit_code') == -2 and s.get('interrupted') is True]
    no_launch = not segments
    control = 'control_cli_error' in reasons and bool(entry.get('control_error'))
    capacity = bool(entry.get('infrastructure_stop') and
                    'at capacity' in entry['infrastructure_stop'].lower() and
                    any(s.get('capacity_error') for s in segments))
    if not (no_launch and control or interrupted or control or capacity):
        return False
    if 'runner_control_file_preexisting' in reasons and not no_launch:
        return False  # Executor-authored control inputs are never infrastructure.
    allowed_errors = {'missing_logs'} if no_launch else set()
    if interrupted:
        allowed_errors.update({'missing_log', 'missing_logs', 'missing_terminal_event'})
    # Check both historical and current error lists. A parser precision error is
    # recovered by regrade, never by spending on a new executor outcome.
    for observed in (historical, audit):
        for error in observed.get('errors', []):
            kind, _, name = error.partition(':')
            if kind not in allowed_errors:
                return False
            if kind in {'missing_log', 'missing_terminal_event'} and name not in {s['events'] for s in interrupted}:
                return False
    if 'executor_service_tier_missing_or_different' in reasons and not (no_launch or interrupted):
        return False
    return True


def rerun_invalid(private_root: Path, source: Path, out: Path, reasons: set[str], *,
                  execute: Callable[..., ProcessResult] = run_process,
                  version: str | Callable[[], str] | None = None) -> Path:
    """Regrade unselected tasks and launch selected tasks in pristine runtimes."""
    if not reasons or not reasons <= REASONS:
        raise ValueError('Unsupported infrastructure reason selector')
    source, out = source.resolve(), out.resolve()
    if out.exists() or out.is_relative_to(source) or source.is_relative_to(out):
        raise ValueError('A fresh output separate from the source is required')
    source_bytes = (source / 'report.json').read_bytes()
    original = json.loads(source_bytes)
    state = json.loads((source / 'checkpoint.json').read_text())
    config = state['config']
    selected = []
    for task in original['tasks']:
        if task['outcome'] != 'invalid' or not reasons.intersection(task['invalid_reasons']):
            continue
        entry = state['tasks'][task['task_id']]
        runtime = Path(entry['runtime'])
        if (not runtime.is_absolute() or any(Path(s['events']).name != s['events'] for s in entry['segments'])
                or entry.get('pid')):
            raise ValueError('Unsafe or active retained runtime')
        private = PrivateGraders.load(private_root, task['task_id'], core.REPOSITORY, task_root=config.get('task_root'))
        paths = [runtime / s['events'] for s in entry['segments']]
        paths.extend(sorted((runtime / 'codex-home/sessions').rglob('*.jsonl')))
        audit = audit_retained_logs(paths, private, retained_context=entry.get('retained_audit_context'),
                                    interrupted_paths=interrupted_logs(runtime, entry['segments']),
                                    workspace=runtime / 'workspace', repository=core.REPOSITORY,
                                    grading_roots=core.audit_roots(runtime))
        previous_logs = Counter((log['name'], log['sha256'], log['bytes'])
                                for log in entry.get('result', {}).get('grader_access_audit', {}).get('logs', []))
        current_logs = Counter((log['name'], log['sha256'], log['bytes']) for log in audit['logs'])
        if current_logs - previous_logs:
            raise ValueError('Retained log manifest changed')
        if any(a.get('matches') or a.get('status') == 'access_detected' for a in (
                task.get('grader_access_audit', {}), entry.get('result', {}).get('grader_access_audit', {}), audit)):
            raise ValueError('Refused task with access matches')
        if not eligible(task, entry, audit):
            continue  # Precision/quality invalidity is regraded from retained evidence.
        # Never classify modified trusted control bytes as a restart artifact.
        harness.ControlFiles(runtime, entry.get('control_files', {}), lambda: None).verify()
        selected.append(task['task_id'])
    if not selected:
        raise ValueError('No eligible infrastructure-invalid tasks match the requested reasons')
    pricing = json.loads((core.REPOSITORY / 'eval/prices.yaml').read_text())
    if not extends(pricing, original['metadata']['pricing']):
        raise ValueError('Pinned pricing snapshot differs')
    read_version = version if callable(version) else (lambda: version) if version else core.installed_version
    if read_version() != config['codex_version']:
        raise ValueError('Installed Codex version differs')
    core.require_call_estimate(dict(config, tasks=selected))
    # Regrade validates source/config/task-set provenance before creating output.
    # Selected tasks may have no segments/exit hash because no executor launched.
    regrade.regrade(private_root, source, out, execute=execute, _fresh_tasks=frozenset(selected))
    base = json.loads((out / 'report.json').read_text())
    recovered_state = json.loads((out / 'checkpoint.json').read_text())
    source_tasks = {t['task_id']: t for t in original['tasks']}
    provenance = {'source': str(source), 'source_run_id': original['metadata']['run_id'],
                  'source_report_sha256': digest(source_bytes),
                  'source_checkpoint_sha256': digest((source / 'checkpoint.json').read_bytes()),
                  'requested_reasons': sorted(reasons), 'selected_tasks': selected, 'status': 'pending',
                  'audit_code_version': regrade.audit_code_version() | {
                      name: digest((Path(__file__).parent / name).read_bytes())
                      for name in ('core.py', 'harness.py', 'rerun_invalid.py')}, 'tasks': []}
    for task_id in selected:
        old = source_tasks[task_id]
        evidence = {**{k: v for k, v in provenance.items() if k != 'tasks'},
                    'task_id': task_id, 'invalid_reasons': old['invalid_reasons'],
                    'source_executor_segments': old['executor_segments'], 'source_artifacts': old['artifacts'],
                    'source_calls': old['calls'], 'source_costs': old['costs'], 'rerun_id': uuid.uuid4().hex}
        core.write_json(out / task_id / 'rerun-provenance.json', evidence)
        provenance['tasks'].append(evidence)
        recovered_state['tasks'].pop(task_id)
        recovered_state.setdefault('fresh_reruns', {})[task_id] = {
            'rerun_id': evidence['rerun_id'], 'calls': copy.deepcopy(old['calls']),
            'control_usd': old['costs']['control_usd']}
    core.write_json(out / 'checkpoint.json', recovered_state)
    core.write_json(out / 'rerun-invalid.json', provenance)
    config_path = out / 'rerun-config.yaml'
    core.write_json(config_path, config)
    try:
        core.run(config_path, out, private_root, execute=execute, version=read_version,
                 _recorded_config_sha256=state['config_sha256'])
    except (Exception, KeyboardInterrupt):
        provenance['status'] = 'incomplete'
        core.write_json(out / 'rerun-invalid.json', provenance)
        raise
    fresh = json.loads((out / 'report.json').read_text())
    new_by_id = {t['task_id']: t for t in fresh['tasks']}
    base['tasks'] = [new_by_id[t['task_id']] if t['task_id'] in selected else t for t in base['tasks']]
    tasks = base['tasks']
    final_state = json.loads((out / 'checkpoint.json').read_text())
    for evidence in provenance['tasks']:
        task_id = evidence['task_id']
        task = new_by_id[task_id]
        old_ids = {call['call_id'] for call in source_tasks[task_id]['calls']}
        added = [call for call in task['calls'] if call['call_id'] not in old_ids]
        added_control_usd = (control_calls(final_state['tasks'][task_id], task_id, pricing)[1]
                             if config['harness'] else 0)
        added_executor_usd = total([call['usage']['usd'] for call in added if call['purpose'] == 'executor'])
        evidence.update(status='finished', outcome=task['outcome'],
                        fresh_runtime=final_state['tasks'][task_id]['runtime'],
                        added_call_ids=[call['call_id'] for call in added],
                        added_cost_usd=total([added_executor_usd, added_control_usd]))
        path = out / task_id / 'rerun-provenance.json'
        core.write_json(path, evidence)
        pinned = artifact(path)
        task['artifacts'] = [a for a in task['artifacts'] if a['path'] != pinned['path']] + [pinned]
    base['metrics'] = compute(tasks, seed=base['metadata']['confidence']['seed'],
                              resamples=base['metadata']['confidence']['resamples'])
    if all(t['done_claims']['claimed_items'] == 0 for t in tasks):
        base['metrics']['false_done_rate'] = original['metrics']['false_done_rate']
    base['accounting'] = {'attempted_tasks': len(tasks), 'valid_tasks': sum(t['outcome'] != 'invalid' for t in tasks),
                          'invalid_tasks': sum(t['outcome'] == 'invalid' for t in tasks),
                          'total_cost_usd': total([t['costs']['total_usd'] for t in tasks])}
    invalid = [f"{t['task_id']}: {reason}" for t in tasks for reason in t['invalid_reasons']]
    base['validity'] = {'status': 'invalid' if invalid else 'valid', 'reasons': invalid}
    models = {c['model'] for t in tasks for c in t['calls'] if c['purpose'] != 'executor'}
    base['metadata']['control_model'] = next(iter(models)) if len(models) == 1 and 'unknown' not in models else None
    from eval.runner.task_completion import publish_summary
    publish_summary(tasks, out)
    base["metadata"]["pricing"] = report_pricing(pricing)
    validate(base, core.REPOSITORY)
    provenance['status'] = 'finished'
    core.write_json(out / 'rerun-invalid.json', provenance)
    diagnostics = json.loads((out / 'run-diagnostics.json').read_text())
    diagnostics['rerun_invalid'] = provenance
    core.write_json(out / 'run-diagnostics.json', diagnostics)
    core.write_json(out / 'report.json', base)
    return out / 'report.json'


def main() -> int:
    """Print one output directory; keep private paths out of all error messages."""
    parser: argparse.ArgumentParser = InputParser(description=__doc__)
    parser.add_argument('--private-root', type=Path, required=True)
    parser.add_argument('--from', dest='source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--reasons', required=True)
    try:
        args = parser.parse_args()
        with stop_signals(args.out):
            rerun_invalid(args.private_root, args.source, args.out, set(args.reasons.split(',')))
    except KeyboardInterrupt:
        print('Rerun interrupted; checkpoint and stop diagnostics retained', file=sys.stderr)
        return 130
    except (ValueError, FileNotFoundError, KeyError, harness.HarnessError):
        print('Rerun input error: eligible infrastructure evidence or pinned inputs unavailable', file=sys.stderr)
        return 1
    except core.IncompleteRun:
        print('Rerun halted; fresh output retains resumable evidence', file=sys.stderr)
        return 2
    except Exception:
        print('Rerun internal error', file=sys.stderr)
        return 2
    print(str(args.out))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
