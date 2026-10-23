"""Fresh reruns of infrastructure-invalid tasks, retaining all other evidence."""

import argparse
from collections import Counter
import copy
import json
from pathlib import Path
import re
import sys
from typing import Any, Callable
import uuid

from eval.runner.pricing import extends, report_pricing, select
from eval.metrics import compute, total
from eval.runner import core, harness, regrade
from eval.runner.audit import PrivateGraders, audit_retained_logs, digest, interrupted_logs
from eval.runner.process import ProcessResult, run_process
from eval.runner.control_accounting import control_calls
from eval.runner.reaudit import InputParser
from eval.runner.report import artifact, validate, usage as executor_usage
from eval.runner.signals import stop_signals
from eval.runner.publication import safe_source
from eval.runner.telemetry import recover_partial_usage, interrupted_pricing_evidence
from eval.runner.workspace_verification import verify as verify_workspace


REASONS = frozenset({
    'control_cli_error', 'control_timeout', 'runner_control_file_preexisting', 'execution_interrupted',
    'incomplete_access_audit', 'missing_executor_session_id', 'executor_settings_unverified',
    'missing_cli_version_evidence', 'missing_two_session_handoff_observation',
    'executor_service_tier_missing_or_different', 'capacity_exhausted',
})


class RecoveryEligibilityError(ValueError):
    """Safe condition names suitable for CLI diagnostics without private paths."""


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
    control = bool(reasons & {'control_cli_error', 'control_timeout'}) and bool(entry.get('control_error'))
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


def unaccounted_causes(task: dict[str, Any], entry: dict[str, Any],
                       audit: dict[str, Any], pricing: dict[str, Any],
                       native_paths: list[Path] | None = None, *,
                       refusals: list[str] | None = None) -> list[dict[str, Any]]:
    """Select only valid tasks whose sole accounting gap is interrupted usage."""
    result = entry.get('result', {})
    def reject(reason: str) -> list[dict[str, Any]]:
        if refusals is not None:
            refusals.append(reason)
        return []

    conditions = [
        (task.get('outcome') in {'pass', 'fail', 'timeout', 'error'}, 'valid_task_required'),
        (result.get('outcome') == task['outcome'], 'checkpoint_outcome_mismatch'),
        (not task.get('invalid_reasons') and not result.get('invalid_reasons'), 'invalid_reasons_present'),
        (not entry.get('rerun_history'), 'prior_replacement_present'),
        (task.get('costs', {}).get('executor_usd') is None, 'null_executor_cost_required'),
        (task.get('costs', {}).get('total_usd') is None, 'null_total_cost_required'),
        (task.get('costs', {}).get('control_usd') is not None, 'control_cost_missing'),
        (not any(a.get('status') != 'clean' or a.get('matches') or a.get('errors') for a in
                 (task.get('grader_access_audit', {}), result.get('grader_access_audit', {}), audit)),
         'clean_access_audits_required'),
    ]
    for passed, reason in conditions:
        if not passed:
            return reject(reason)
    calls = [c for c in task.get('calls', []) if c['purpose'] == 'executor']
    segments = entry.get('segments', [])
    if len(calls) != len(segments) or not calls:
        return reject('executor_call_segment_count_mismatch')
    if any(c['usage']['usd'] is None for c in task['calls'] if c['purpose'] != 'executor'):
        return reject('control_usage_missing')
    causes = []
    for index, (call, segment) in enumerate(zip(calls, segments)):
        if call['call_id'] != f"{task['task_id']}-exec-{segment['attempt']}":
            return reject('executor_call_segment_identity_mismatch')
        usage = call['usage']
        if usage['usd'] is not None:
            continue
        missing = [k for k in ('input_tokens', 'cached_input_tokens', 'output_tokens')
                   if usage.get(k) is None]
        if not missing:
            return reject('missing_executor_usage_required')
        # Historical pricing may also be unknown when an interrupted process
        # retained no usage. Archive it without imputing any historical cost.
        price_evidence = segment.get('pricing_evidence')
        if price_evidence is None:
            price_evidence = interrupted_pricing_evidence(segment, native_paths or [])
        tier = (price_evidence or {}).get('tier')
        _, reference = select(pricing, call['model'], tier)
        observed = executor_usage(Path(entry['runtime']) / segment['events'], 0, call['model'], pricing,
                                  tier=tier, native_counts=segment.get('native_usage'))
        if all(observed.get(k) is not None for k in ('input_tokens', 'cached_input_tokens', 'output_tokens')):
            return reject('complete_executor_usage_recoverable')
        markers = [key for key in ('interrupted', 'capacity_error') if segment.get(key) is True]
        if segment.get('exit_code') == -2:
            markers.append('exit_code=-2')
        if segment.get('infrastructure_recovery') is True and any(
                s.get('capacity_error') is True for s in segments[:index]):
            markers.append('capacity_recovery')
        if not markers:
            return reject('infrastructure_interruption_marker_missing')
        causes.append({'attempt': segment['attempt'], 'events': segment['events'],
                       'markers': markers, 'missing_usage_fields': missing,
                       'pricing_ref': reference, 'pricing_evidence': price_evidence})
    return causes or reject('missing_executor_usage_required')


def rerun_invalid(private_root: Path, source: Path, out: Path, reasons: set[str], *,
                  execute: Callable[..., ProcessResult] = run_process,
                  version: str | Callable[[], str] | None = None,
                  _unaccounted: bool = False) -> Path:
    """Regrade unselected tasks and launch selected tasks in pristine runtimes."""
    if (not _unaccounted and (not reasons or not reasons <= REASONS)) or (_unaccounted and reasons):
        raise ValueError('Unsupported infrastructure reason selector')
    source, out = source.resolve(), out.resolve()
    if out.exists() or out.is_relative_to(source) or source.is_relative_to(out):
        raise ValueError('A fresh output separate from the source is required')
    source_bytes = (source / 'report.json').read_bytes()
    original = json.loads(source_bytes)
    state = json.loads((source / 'checkpoint.json').read_text())
    config = state['config']
    selected = []
    causes_by_task = {}
    workspace_checks = {}
    refusals = []
    for task in original['tasks']:
        candidate = (task['outcome'] != 'invalid' and task['costs']['executor_usd'] is None
                     if _unaccounted else task['outcome'] == 'invalid' and reasons.intersection(task['invalid_reasons']))
        if not candidate:
            continue
        entry = state['tasks'][task['task_id']]
        runtime = Path(entry['runtime'])
        if (not runtime.is_absolute() or any(Path(s['events']).name != s['events'] for s in entry['segments'])
                or entry.get('pid')):
            raise RecoveryEligibilityError('unsafe_or_active_retained_runtime')
        private = PrivateGraders.load(private_root, task['task_id'], core.REPOSITORY, task_root=config.get('task_root'))
        paths = [runtime / s['events'] for s in entry['segments']]
        paths.extend(sorted((runtime / 'codex-home/sessions').rglob('*.jsonl')))
        if not safe_source(runtime, runtime) or any(not safe_source(p, runtime) for p in paths):
            raise RecoveryEligibilityError('unsafe_retained_evidence')
        if _unaccounted or "workspace_exit_sha256" in entry:
            verification = verify_workspace(runtime / 'workspace', entry, task,
                                            published_workspace=source / task['task_id'] / 'workspace')
            if verification is None:
                raise RecoveryEligibilityError('Workspace exit hash mismatch: workspace_verification_failed')
            workspace_checks[task['task_id']] = verification
        audit = audit_retained_logs(paths, private, retained_context=entry.get('retained_audit_context'),
                                    interrupted_paths=interrupted_logs(runtime, entry['segments']),
                                    workspace=runtime / 'workspace', repository=core.REPOSITORY,
                                    grading_roots=core.audit_roots(runtime))
        previous_logs = Counter((log['name'], log['sha256'], log['bytes'])
                                for log in entry.get('result', {}).get('grader_access_audit', {}).get('logs', []))
        current_logs = Counter((log['name'], log['sha256'], log['bytes']) for log in audit['logs'])
        if current_logs - previous_logs or (_unaccounted and current_logs != previous_logs):
            raise RecoveryEligibilityError('Retained log manifest changed: retained_log_manifest_mismatch')
        if any(a.get('matches') or a.get('status') == 'access_detected' for a in (
                task.get('grader_access_audit', {}), entry.get('result', {}).get('grader_access_audit', {}), audit)):
            raise RecoveryEligibilityError('Refused task with access matches: clean_access_audits_required')
        failed = []
        causes = unaccounted_causes(task, entry, audit, original['metadata']['pricing'],
                                   paths[len(entry['segments']):], refusals=failed) if _unaccounted else []
        if failed:
            identity = task['task_id'] if re.fullmatch(r'[a-z0-9][a-z0-9-]*', task['task_id']) else 'invalid_task_id'
            refusals.extend(f'{identity}: {reason}' for reason in failed)
        if not (bool(causes) if _unaccounted else eligible(task, entry, audit)):
            continue  # Precision/quality invalidity is regraded from retained evidence.
        # Never classify modified trusted control bytes as a restart artifact.
        harness.ControlFiles(runtime, entry.get('control_files', {}), lambda: None).verify()
        if _unaccounted:
            recover_partial_usage(entry['segments'], paths[len(entry['segments']):])
            causes_by_task[task['task_id']] = causes
        selected.append(task['task_id'])
    if not selected:
        detail = '; '.join(sorted(set(refusals or ['valid_task_with_null_executor_cost_required']))) if _unaccounted else ''
        raise RecoveryEligibilityError('No eligible infrastructure tasks match the requested recovery' +
                                       (': ' + detail if detail else ''))
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
    operation = 'rerun-unaccounted' if _unaccounted else 'rerun-invalid'
    provenance_path = out / f'{operation}.json'
    provenance = {'operation': operation, 'source': str(source), 'source_run_id': original['metadata']['run_id'],
                  'source_report_sha256': digest(source_bytes),
                  'source_checkpoint_sha256': digest((source / 'checkpoint.json').read_bytes()),
                  'requested_reasons': sorted(reasons), 'selected_tasks': selected, 'status': 'pending',
                  'audit_code_version': regrade.audit_code_version() | {
                      name: digest((Path(__file__).parent / name).read_bytes())
                      for name in ('core.py', 'harness.py', 'rerun_invalid.py', 'rerun_unaccounted.py')}, 'tasks': []}
    for task_id in selected:
        old = source_tasks[task_id]
        evidence = {**{k: v for k, v in provenance.items() if k != 'tasks'},
                    'task_id': task_id, 'invalid_reasons': old['invalid_reasons'],
                    'source_outcome': old['outcome'],
                    'reason': 'executor_usage_missing_after_infrastructure_interruption' if _unaccounted else 'infrastructure_invalidity',
                    'accounting_policy': 'replace_with_fresh_session' if _unaccounted else 'retain_prior_spending',
                    'infrastructure_causes': causes_by_task.get(task_id, []),
                    'source_segments': state['tasks'][task_id]['segments'],
                    'source_executor_segments': old['executor_segments'], 'source_artifacts': old['artifacts'],
                    'source_calls': old['calls'], 'source_costs': old['costs'], 'rerun_id': uuid.uuid4().hex}
        evidence.update(workspace_checks.get(task_id, {}))
        core.write_json(out / task_id / 'rerun-provenance.json', evidence)
        provenance['tasks'].append(evidence)
        recovered_state['tasks'].pop(task_id)
        recovered_state.setdefault('fresh_reruns', {})[task_id] = {
            'rerun_id': evidence['rerun_id'], 'calls': [] if _unaccounted else copy.deepcopy(old['calls']),
            'control_usd': 0 if _unaccounted else old['costs']['control_usd']}
    core.write_json(out / 'checkpoint.json', recovered_state)
    core.write_json(provenance_path, provenance)
    config_path = out / 'rerun-config.yaml'
    core.write_json(config_path, config)
    try:
        core.run(config_path, out, private_root, execute=execute, version=read_version,
                 _recorded_config_sha256=state['config_sha256'])
    except (Exception, KeyboardInterrupt):
        provenance['status'] = 'incomplete'
        core.write_json(provenance_path, provenance)
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
    core.write_json(provenance_path, provenance)
    diagnostics = json.loads((out / 'run-diagnostics.json').read_text())
    diagnostics[operation.replace('-', '_')] = provenance
    core.write_json(out / 'run-diagnostics.json', diagnostics)
    core.write_json(out / 'report.json', base)
    return out / 'report.json'


def main(*, _unaccounted: bool = False) -> int:
    """Print one output directory; keep private paths out of all error messages."""
    parser: argparse.ArgumentParser = InputParser(description=(
        'Fresh replacement of valid tasks with interruption-only missing executor usage.' if _unaccounted else __doc__))
    parser.add_argument('--private-root', type=Path, required=True)
    parser.add_argument('--from', dest='source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    if not _unaccounted:
        parser.add_argument('--reasons', required=True)
    try:
        args = parser.parse_args()
        with stop_signals(args.out):
            if _unaccounted:
                rerun_invalid(args.private_root, args.source, args.out, set(), _unaccounted=True)
            else:
                rerun_invalid(args.private_root, args.source, args.out, set(args.reasons.split(',')))
    except KeyboardInterrupt:
        print('Rerun interrupted; checkpoint and stop diagnostics retained', file=sys.stderr)
        return 130
    except RecoveryEligibilityError as exc:
        print('Rerun input error: ' + str(exc), file=sys.stderr)
        return 1
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
