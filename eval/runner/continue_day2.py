"""Continue audit-recoverable two-session tasks in fresh external runtimes."""

import argparse
import copy
from datetime import datetime
import json
import os
import re
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Callable

from eval.runner.pricing import extends, report_pricing
from eval.metrics import compute, total
from eval.runner import core, harness, reaudit, regrade
from eval.runner.audit import PrivateGraders, digest
from eval.runner.process import ProcessResult, run_process
from eval.runner.signals import stop_signals
from eval.runner.control_accounting import control_calls
from eval.runner.report import artifact, validate
from eval.runner.publication import safe_source
from eval.runner.workspace_verification import verify as verify_workspace
from eval.runner.day1_recovery import pending_verification


RECOVERABLE = {'incomplete_access_audit', 'missing_two_session_handoff_observation'}


def eligible(task: dict[str, Any], entry: dict[str, Any], config: dict[str, Any] | None = None) -> bool:
    """Require only the two causal invalid reasons and consistent day-1 evidence."""
    result = entry.get('result', {})
    audit = result.get('grader_access_audit', {})
    segments = entry.get('segments', [])
    return bool(task.get('two_session') and result.get('two_session') and
                task.get('outcome') == result.get('outcome') == 'invalid' and
                set(task.get('invalid_reasons', [])) == set(result.get('invalid_reasons', [])) == RECOVERABLE and
                task.get('grader_access_audit', {}).get('status') == audit.get('status') == 'inconclusive' and
                not audit.get('matches') and not entry.get('day2_observation') and
                not result.get('day2_observation') and not result.get('grading') and
                segments and result.get('segments') == segments and not entry.get('retained_audit_context') and
                len(task.get('executor_segments', [])) == len(segments) and
                all(all(s.get(key) == published.get(key) for key in ('attempt', 'started_at', 'exited_at', 'exit_code'))
                    for s, published in zip(segments, task['executor_segments'])) and
                (pending_verification(entry, config or {}) or
                 (all(s.get('day', 1) == 1 and type(s.get('exit_code')) is int and
                      re.fullmatch(r'[0-9a-f]{64}', s.get('workspace_exit_sha256', '')) for s in segments) and
                  segments[-1]['workspace_exit_sha256'] == entry.get('workspace_exit_sha256'))))


def copy_runtime(entry: dict[str, Any], private: PrivateGraders,
                 task: dict[str, Any] | None = None, *,
                 published_workspace: Path | None = None) -> dict[str, Any]:
    """Copy workspace and allowlisted public evidence; never copy grading artifacts."""
    old = Path(entry['runtime'])
    workspace = old / 'workspace'
    if not safe_source(workspace, old) or not workspace.is_dir():
        raise ValueError('Continuation refused: unsafe workspace root')
    # Absolute/outward links could let a new executor mutate retained evidence.
    for path in workspace.rglob('*'):
        if path.is_symlink() and (Path(os.readlink(path)).is_absolute() or
                                  not path.resolve().is_relative_to(workspace.resolve())):
            raise ValueError('Continuation refused: workspace contains an external symlink')
    guard = harness.ControlFiles(old, entry.get('control_files', {}), lambda: None)
    guard.verify()
    names = set(entry.get('control_files', {}))
    logs = {s['events'] for s in entry['segments']}
    logs.update(str(p.relative_to(old)) for p in (old / 'codex-home/sessions').rglob('*.jsonl'))
    names.update(logs)
    for segment in entry['segments']:
        names.add(segment['stderr'])
        final = f"final-{segment['attempt']}.md"
        if (old / final).exists():
            names.add(final)
    for name in names:
        path = old / name
        if (Path(name).is_absolute() or '..' in Path(name).parts or not guard.safe(path) or
                not path.is_file() or path.is_symlink()):
            raise ValueError('Continuation refused: unsafe retained evidence')
    auth = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    if not auth.is_file():
        raise ValueError('Continuation requires the existing CLI login')
    runtime = Path(tempfile.mkdtemp(prefix='lhm-eval-continue-')).resolve()
    if (runtime.is_relative_to(core.REPOSITORY.resolve()) or runtime.is_relative_to(private.root.resolve()) or
            runtime.is_relative_to(old.resolve()) or old.resolve().is_relative_to(runtime)):
        raise ValueError('Continuation runtime must be separate from repository, source and private storage')
    shutil.copytree(workspace, runtime / 'workspace', symlinks=True)
    expected = entry['workspace_exit_sha256']
    verification = verify_workspace(workspace, entry, task, published_workspace=published_workspace)
    if (verification is None or verify_workspace(runtime / 'workspace', entry, task,
                                                published_workspace=published_workspace) is None):
        raise ValueError('Continuation refused: copied day-1 workspace exit hash mismatch')
    for name in names:
        target = runtime / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old / name, target)
    (runtime / 'codex-home/sessions').mkdir(parents=True, exist_ok=True)
    (runtime / 'codex-home/auth.json').symlink_to(auth.resolve())
    copied = copy.deepcopy(entry)
    copied.update(runtime=str(runtime), phase='ready', active_day=1, completed_days=[1], transport_retries=0)
    for key in ('result', 'pid', 'reinstruction', 'pending_verification'):
        copied.pop(key, None)
    # Paths in logs remain byte-for-byte historical; only manifest references move.
    for segment in copied['segments']:
        segment['native_logs'] = [str(runtime / Path(p).relative_to(old)) for p in segment.get('native_logs', [])]
    copied['retained_audit_context'] = {
        'runtime': str(old), 'copied_runtime': str(runtime), 'workspace': str(workspace),
        'workspace_exit_sha256': expected,
        **({'workspace_digest_version': entry['workspace_digest_version']}
           if 'workspace_digest_version' in entry else {}),
        'grading_roots': [str(p) for p in core.audit_roots(old)],
        'logs': {str(runtime / name): digest((old / name).read_bytes()) for name in logs}}
    if verification['workspace_verification'] != 'workspace_digest' and task is not None:
        copied['retained_audit_context']['workspace_artifact_evidence'] = {
            key: copy.deepcopy(task[key]) for key in ('task_id', 'artifacts', 'executor_segments')}
        copied['retained_audit_context']['workspace_verification'] = verification
        if verification['workspace_verification'] == 'published_workspace_copy':
            copied['retained_audit_context']['published_workspace'] = str(published_workspace)
        copied['retained_audit_context']['workspace_copy'] = {
            'sha256': core.workspace_digest(runtime / 'workspace'),
            'digest_version': core.WORKSPACE_DIGEST_VERSION}
    return copied


def continue_day2(private_root: Path, source: Path, out: Path, *,
                  execute: Callable[..., ProcessResult] = run_process,
                  version: str | Callable[[], str] | None = None) -> Path:
    """Regrade other tasks, then reuse the normal runner for copied day-1 state."""
    source, out = source.resolve(), out.resolve()
    if out.exists() or out.is_relative_to(source) or source.is_relative_to(out):
        raise ValueError('Continuation requires a fresh directory separate from the source')
    original_bytes = (source / 'report.json').read_bytes()
    original = json.loads(original_bytes)
    source_state = json.loads((source / 'checkpoint.json').read_text())
    config = source_state['config']
    candidates = {task['task_id'] for task in original['tasks']
                  if eligible(task, source_state['tasks'][task['task_id']], config)}
    rows = {row['task_id']: row for row in reaudit.reaudit(private_root, source)}
    selected = sorted(task for task in candidates if rows[task]['status'] == 'clean')
    if not selected:
        raise ValueError('Continuation refused: no audit-recoverable day-1 task')
    recovering = frozenset(task for task in selected
                           if pending_verification(source_state['tasks'][task], config))
    pricing = json.loads((core.REPOSITORY / 'eval/prices.yaml').read_text())
    if not extends(pricing, original['metadata']['pricing']):
        raise ValueError('Continuation refused: recorded pricing snapshot differs')
    read_version = version if callable(version) else (lambda: version) if version else core.installed_version
    if read_version() != config['codex_version']:
        raise ValueError('Continuation refused: installed Codex version differs')
    estimate = core.require_call_estimate(dict(config, tasks=selected), recovery=True)
    estimate['reasons'] = sorted(RECOVERABLE)
    # Regrade validates source/report/task-set provenance and historical pins.
    # Audit-blocked tasks may have only the preceding attempt's
    # exit pin. Regrade validates their run/task provenance but leaves them for
    # the explicitly recorded post-exit verification below.
    regrade.regrade(private_root, source, out, execute=execute, _fresh_tasks=recovering)
    base_report = json.loads((out / 'report.json').read_text())
    diagnostics = json.loads((out / 'run-diagnostics.json').read_text())
    state = json.loads((out / 'checkpoint.json').read_text())
    source_tasks = {task['task_id']: task for task in original['tasks']}
    prepared = copy.deepcopy(source_state['tasks'])
    for task in selected:
        private = PrivateGraders.load(private_root, task, core.REPOSITORY, task_root=config.get('task_root'))
        retained = prepared[task]
        if task in recovering:
            last = retained['segments'][-1]
            recovery = {'attempt': last['attempt'], 'executor_exited_at': last['exited_at'],
                        'snapshot_recorded_at': core.now(), 'verification_after_exit': True,
                        'historical_exit_hash_available': 'workspace_exit_sha256' in last,
                        'prior_workspace_exit_sha256': retained.get('workspace_exit_sha256')}
            workspace = Path(retained['runtime']) / 'workspace'
            if 'workspace_exit_sha256' in last:
                if (last['workspace_exit_sha256'] != retained.get('workspace_exit_sha256') or
                        verify_workspace(workspace, retained, source_tasks[task],
                                         published_workspace=source / task / 'workspace') is None):
                    raise ValueError('Continuation refused: retained attempt exit hash mismatch')
            else:
                core.record_workspace_exit(workspace, retained, last)
            recovery['recovery_workspace_sha256'] = core.workspace_digest(workspace)
            recovery['workspace_digest_version'] = core.WORKSPACE_DIGEST_VERSION
            retained['day1_verification_recovery'] = recovery
        state['tasks'][task] = copy_runtime(retained, private, source_tasks[task],
                                           published_workspace=source / task / 'workspace')
        if task in recovering:
            state['tasks'][task].update(completed_days=[], pending_verification=True)
    core.write_json(out / 'checkpoint.json', state)
    config_path = out / 'continuation-config.yaml'
    core.write_json(config_path, config)
    provenance = {
        'source': str(source), 'source_report_sha256': digest(original_bytes),
        'source_run_id': original['metadata']['run_id'],
        'audit_code_version': regrade.audit_code_version() | {
            name: digest((Path(__file__).parent / name).read_bytes())
            for name in ('core.py', 'harness.py', 'continue_day2.py', 'day1_recovery.py', 'reaudit.py')},
        'recorded_config_sha256': source_state['config_sha256'],
        'materialized_config_sha256': digest(config_path.read_bytes()),
        'selected_tasks': selected, 'status': 'pending', 'tasks': [], 'cost_estimate': estimate}
    core.write_json(out / 'continuation.json', provenance)
    try:
        core.run(config_path, out, private_root, execute=execute, version=read_version,
                 _recorded_config_sha256=source_state['config_sha256'])
    except (Exception, KeyboardInterrupt):
        provenance['status'] = 'incomplete'
        core.write_json(out / 'continuation.json', provenance)
        raise
    finally:
        current_diagnostics = json.loads((out / 'run-diagnostics.json').read_text())
        current_diagnostics['recovery_estimate'] = estimate
        core.write_json(out / 'run-diagnostics.json', current_diagnostics)
    diagnostics['recovery_estimate'] = estimate
    state = json.loads((out / 'checkpoint.json').read_text())
    resumed = json.loads((out / 'report.json').read_text())
    new_by_id = {t['task_id']: t for t in resumed['tasks']}
    old_by_id = {t['task_id']: t for t in original['tasks']}
    for index, task in enumerate(base_report['tasks']):
        task_id = task['task_id']
        if task_id not in selected:
            continue
        continued, old = new_by_id[task_id], old_by_id[task_id]
        entry = state['tasks'][task_id]
        old_ids = {call['call_id'] for call in old['calls']}
        extra = [call for call in continued['calls'] if call['purpose'] == 'executor' and call['call_id'] not in old_ids]
        # Control call IDs are ordinal in filename order. New day-2 files can
        # sort before an existing handoff, so price only newly produced streams
        # and give their calls a separate ID namespace.
        prior_controls = source_state['tasks'][task_id].get('control_files', {})
        added_entry = dict(entry, control_files={name: value for name, value in entry.get('control_files', {}).items()
                                                if name not in prior_controls})
        control_provenance: list[dict[str, Any]] = []
        added_controls, added_control_usd = (control_calls(added_entry, task_id, pricing, provenance=control_provenance)
                                             if config['harness'] else ([], 0))
        for row in control_provenance:
            row["call_id"] = row["call_id"].replace("-control-", "-continuation-control-", 1)
        for call in added_controls:
            call['call_id'] = call['call_id'].replace('-control-', '-continuation-control-', 1)
        extra.extend(added_controls)
        from eval.runner.pricing import reprice_retained_calls
        recovered = copy.deepcopy(old)
        historical_provenance = reprice_retained_calls(recovered, source_state['tasks'][task_id],
                                                      original['metadata']['pricing'])
        continued['calls'] = recovered['calls'] + extra
        executor_usd = total([c['usage']['usd'] for c in continued['calls'] if c['purpose'] == 'executor'])
        control_usd = total([recovered['costs']['control_usd'], added_control_usd])
        continued['costs'] = {'executor_usd': executor_usd, 'control_usd': control_usd,
                              'total_usd': total([executor_usd, control_usd])}
        continued['done_claims'] = copy.deepcopy(old['done_claims'])
        from eval.runner.pricing import preserve_provenance
        preserve_provenance(continued, out / task_id, prior=old, pricing=pricing,
                            additional=historical_provenance + control_provenance)
        entry = state['tasks'][task_id]
        day1 = [s for s in entry['segments'] if s.get('day', 1) == 1]
        day2 = [s for s in entry['segments'] if s.get('day') == 2]
        gap = ((datetime.fromisoformat(day2[0]['started_at']) - datetime.fromisoformat(day1[-1]['exited_at'])).total_seconds()
               if day2 else None)
        evidence = {
            'task_id': task_id, 'source_run_id': original['metadata']['run_id'],
            'source': str(source), 'audit_code_version': provenance['audit_code_version'],
            'day1_started_at': day1[0]['started_at'], 'day1_exited_at': day1[-1]['exited_at'],
            'day2_started_at': day2[0]['started_at'] if day2 else None,
            'day2_exited_at': day2[-1]['exited_at'] if day2 else None, 'gap_seconds': gap,
            'day1_workspace_exit_sha256': prepared[task_id]['workspace_exit_sha256'],
            'copied_workspace_sha256': day1[-1]['workspace_exit_sha256'], 'copy_hash_matched': True,
            'added_call_ids': [call['call_id'] for call in extra],
            'added_cost_usd': total([call['usage']['usd'] for call in extra])}
        evidence.update(entry.get('retained_audit_context', {}).get('workspace_verification', {}))
        if task_id in recovering:
            evidence['day1_verification_recovery'] = entry['day1_verification_recovery']
        if evidence.get('workspace_verification') in {'published_artifact_hashes', 'published_workspace_copy'}:
            observed_copy = entry['retained_audit_context']['workspace_copy']
            evidence.update(copied_workspace_sha256=observed_copy['sha256'],
                            copied_workspace_digest_version=observed_copy['digest_version'],
                            copy_hash_matched=False)
        core.write_json(out / task_id / 'continuation.json', evidence)
        entry['continuation'] = evidence
        continued['artifacts'].append(artifact(out / task_id / 'continuation.json'))
        provenance['tasks'].append(evidence)
        base_report['tasks'][index] = continued
    tasks = base_report['tasks']
    base_report['metrics'] = compute(tasks, seed=base_report['metadata']['confidence']['seed'],
                                     resamples=base_report['metadata']['confidence']['resamples'])
    if all(t['done_claims']['claimed_items'] == 0 for t in tasks):
        base_report['metrics']['false_done_rate'] = original['metrics']['false_done_rate']
    base_report['accounting'] = {
        'attempted_tasks': len(tasks), 'valid_tasks': sum(t['outcome'] != 'invalid' for t in tasks),
        'invalid_tasks': sum(t['outcome'] == 'invalid' for t in tasks),
        'total_cost_usd': total([t['costs']['total_usd'] for t in tasks])}
    reasons = [f"{t['task_id']}: {reason}" for t in tasks for reason in t['invalid_reasons']]
    base_report['validity'] = {'status': 'invalid' if reasons else 'valid', 'reasons': reasons}
    # Config/bootstrap and historical prices remain pinned; additional tier
    # snapshots cover only fresh calls.
    # the new run ID and timestamp came from regrade.
    models = {c['model'] for t in tasks for c in t['calls'] if c['purpose'] != 'executor'}
    base_report['metadata']['control_model'] = next(iter(models)) if len(models) == 1 and 'unknown' not in models else None
    from eval.runner.task_completion import publish_summary
    publish_summary(tasks, out)
    base_report["metadata"]["pricing"] = report_pricing(pricing)
    validate(base_report, core.REPOSITORY)
    provenance['status'] = 'finished'
    diagnostics['continuation'] = provenance
    core.write_json(out / 'continuation.json', provenance)
    core.write_json(out / 'run-diagnostics.json', diagnostics)
    core.write_json(out / 'checkpoint.json', state)
    core.write_json(out / 'report.json', base_report)
    return out / 'report.json'


def main() -> int:
    """Print only the new directory on success; keep private locations out of errors."""
    parser: argparse.ArgumentParser = reaudit.InputParser(description=__doc__)
    parser.add_argument('--private-root', type=Path, required=True)
    parser.add_argument('--from', dest='source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    try:
        args = parser.parse_args()
        with stop_signals(args.out):
            continue_day2(args.private_root, args.source, args.out)
    except (ValueError, FileNotFoundError, KeyError):
        print('Continuation input error: eligible retained evidence or pinned configuration unavailable', file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('Continuation interrupted; stop diagnostics retained', file=sys.stderr)
        return 130
    except core.IncompleteRun:
        print('Continuation halted; fresh output retains incomplete evidence for host review', file=sys.stderr)
        return 2
    except Exception:
        print('Continuation internal error', file=sys.stderr)
        return 2
    print(str(args.out))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
