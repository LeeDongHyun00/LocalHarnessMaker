"""Offline replacement of interruption-only accounting gaps and provenance."""

import copy
from datetime import datetime, timedelta
import json
from pathlib import Path
from typing import Any

import pytest

from eval.runner import core, regrade, report as reports, rerun_invalid, rerun_unaccounted
from eval.runner.audit import audit_retained_logs, PrivateGraders, digest, interrupted_logs
from eval.runner.process import ProcessResult, run_process
from eval.runner.telemetry import collect_runs
from tests.eval.test_runner import Executor, setup, two_task_config
from tests.eval.test_restart_recovery import VERSION


def unaccounted_source(setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
                       tmp_path: Path) -> tuple[Path, Path, Path]:
    """Retain one interrupted process followed by a successful resume."""
    root, config, out = setup
    two_task_config(root, config, monkeypatch, tmp_path)
    original = json.loads(core.run(config, out, root, execute=Executor(), version=VERSION).read_text())
    state = json.loads((out / 'checkpoint.json').read_text())
    entry = state['tasks']['bug-chunk-tail']
    runtime = Path(entry['runtime'])
    first = entry['segments'][0]
    second = copy.deepcopy(first)
    second.update(attempt=2, events='exec-2.jsonl', stderr='exec-2.stderr')
    (runtime / second['events']).write_bytes((runtime / first['events']).read_bytes())
    (runtime / second['stderr']).write_text('')
    end = datetime.fromisoformat(first['started_at']) - timedelta(seconds=2)
    first.update(started_at=(end - timedelta(seconds=2)).isoformat(), exited_at=end.isoformat(),
                 exit_code=-2, interrupted=True)
    (runtime / first['events']).write_text('{"type":"thread.started","thread_id":"unit-session"}\n')
    first['evidence_sha256'] = {'exec-1.jsonl': digest((runtime / first['events']).read_bytes())}
    native = runtime / 'codex-home/sessions/rollout-unit.jsonl'
    with native.open('a') as stream:
        stream.write(json.dumps({'type': 'event_msg', 'timestamp': (end - timedelta(seconds=1)).isoformat(),
            'payload': {'type': 'token_count', 'info': {'total_token_usage': {
                'input_tokens': 17, 'cached_input_tokens': 2, 'output_tokens': 4,
                'reasoning_output_tokens': 3, 'total_tokens': 21}}}}) + '\n')
    entry['segments'].append(second)
    private = PrivateGraders.load(root, 'bug-chunk-tail', core.REPOSITORY)
    paths = [runtime / s['events'] for s in entry['segments']]
    audit = audit_retained_logs(paths + [native], private, workspace=runtime / 'workspace',
        repository=core.REPOSITORY, grading_roots=core.audit_roots(runtime),
        interrupted_paths=interrupted_logs(runtime, entry['segments']))
    assert audit['status'] == 'clean', audit
    result = entry['result']
    result.update(segments=copy.deepcopy(entry['segments']), attempts=2, grader_access_audit=audit,
                  executor_runs=collect_runs(paths, [native], entry['segments']))
    core.write_json(out / 'bug-chunk-tail/result.json', result)
    tasks = [reports.build_task(state['tasks'][t['task_id']]['result'], state['tasks'][t['task_id']],
        out / t['task_id'], state['config'], original['metadata']['pricing'], t) for t in original['tasks']]
    original = reports.build(state['config'], state, tasks, VERSION, Path(__file__).resolve().parents[2])
    core.write_json(out / 'checkpoint.json', state)
    core.write_json(out / 'report.json', original)
    assert original['validity']['status'] == 'valid'
    assert original['accounting']['total_cost_usd'] is None
    return root, config, out


@pytest.mark.parametrize('fresh_fail', [False, True])
def test_fresh_replacement_regrades_rest_and_survives_recovery(setup: tuple[Path, Path, Path],
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fresh_fail: bool) -> None:
    root, _, source = unaccounted_source(setup, monkeypatch, tmp_path)
    original = json.loads((source / 'report.json').read_text())
    state = json.loads((source / 'checkpoint.json').read_text())
    before = {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()}
    source_runtime = Path(state['tasks']['bug-chunk-tail']['runtime'])
    original_runtime = {p.relative_to(source_runtime): p.read_bytes() for p in source_runtime.rglob('*')
                        if p.is_file() and not p.is_symlink()}
    executor = Executor()
    grades = []

    def execute(argv: list[str], **kwargs: Any) -> ProcessResult:
        if argv[0] != 'codex':
            grades.append(kwargs['cwd'])
            return run_process(argv, **kwargs)
        assert 'resume' not in argv and kwargs['cwd'].parent != source_runtime
        assert 'len(items) - 1' in (kwargs['cwd'] / 'chunking.py').read_text()
        result = executor(argv, **kwargs)
        if fresh_fail:
            path = kwargs['cwd'] / 'chunking.py'
            path.write_text(path.read_text().replace('len(items)', 'len(items) - 1'))
        return result

    out = tmp_path / 'replaced'
    new = json.loads(rerun_unaccounted.rerun_unaccounted(root, source, out,
        execute=execute, version=VERSION).read_text())
    assert executor.calls == 1 and len(grades) == 2
    selected = next(t for t in new['tasks'] if t['task_id'] == 'bug-chunk-tail')
    old = next(t for t in original['tasks'] if t['task_id'] == selected['task_id'])
    other_old = next(t for t in original['tasks'] if t['task_id'] != selected['task_id'])
    other = next(t for t in new['tasks'] if t['task_id'] != selected['task_id'])
    assert selected['outcome'] == ('fail' if fresh_fail else 'pass')
    assert selected['attempts'] == len(selected['executor_segments']) == len(selected['calls']) == 1
    assert selected['costs']['total_usd'] == pytest.approx(0.0001105)
    assert other['calls'] == other_old['calls'] and other['costs'] == other_old['costs']
    assert new['accounting']['total_cost_usd'] == pytest.approx(0.000221)
    if fresh_fail:
        assert new['metrics']['cost_per_pass']['value'] is None  # zero-pass bootstrap resamples
    else:
        assert new['metrics']['cost_per_pass']['value'] == pytest.approx(0.0001105)
    evidence = json.loads((out / selected['task_id'] / 'rerun-provenance.json').read_text())
    assert evidence['source_outcome'] == 'pass' and evidence['source_costs'] == old['costs']
    assert evidence['source_calls'] == old['calls']
    assert evidence['accounting_policy'] == 'replace_with_fresh_session'
    assert evidence['reason'] == 'executor_usage_missing_after_infrastructure_interruption'
    assert evidence['infrastructure_causes'][0]['attempt'] == 1
    partial = evidence['source_segments'][0]['partial_usage']
    assert partial['lower_bound'] is True and partial['rollouts'][0]['tokens']['input_tokens'] == 17
    assert any(Path(a['path']).name == 'rerun-provenance.json' for a in selected['artifacts'])
    summary = json.loads((out / 'rerun-unaccounted.json').read_text())
    assert summary['selected_tasks'] == [selected['task_id']] and summary['status'] == 'finished'
    assert json.loads((out / 'run-diagnostics.json').read_text())['rerun_unaccounted'] == summary
    assert before == {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()}
    assert original_runtime == {p.relative_to(source_runtime): p.read_bytes() for p in source_runtime.rglob('*')
                                if p.is_file() and not p.is_symlink()}
    # A resumed checkpoint and another retained regrade keep only replacement accounting.
    executor.finished = True
    again = json.loads(core.run(out / 'rerun-config.yaml', out, root, execute=execute, version=VERSION,
        _recorded_config_sha256=state['config_sha256']).read_text())
    assert executor.calls == 1 and again['accounting'] == new['accounting']
    graded = json.loads(regrade.regrade(root, out, tmp_path / 'regraded', execute=execute).read_text())
    assert graded['accounting'] == new['accounting']
    assert any(Path(a['path']).name == 'rerun-provenance.json' for a in graded['tasks'][0]['artifacts'])


@pytest.mark.parametrize('marker', ['interrupted', 'exit_code', 'capacity_error', 'capacity_recovery'])
def test_unaccounted_marker_eligibility(setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
                                      tmp_path: Path, marker: str) -> None:
    _, _, source = unaccounted_source(setup, monkeypatch, tmp_path)
    report = json.loads((source / 'report.json').read_text())
    state = json.loads((source / 'checkpoint.json').read_text())
    task = report['tasks'][0]
    entry = state['tasks'][task['task_id']]
    first = entry['segments'][0]
    first.update(interrupted=False, exit_code=1)
    if marker == 'exit_code':
        first['exit_code'] = -2
    elif marker == 'capacity_recovery':
        # The missing-usage process follows an observed capacity refusal.
        entry['segments'].reverse()
        task['calls'].reverse()
        entry['segments'][0]['capacity_error'] = True
        first['infrastructure_recovery'] = True
    else:
        first[marker] = True
    assert rerun_invalid.unaccounted_causes(task, entry, entry['result']['grader_access_audit'],
                                           report['metadata']['pricing'])


@pytest.mark.parametrize('case', ['no_marker', 'price_only', 'unknown_price', 'unknown_tier', 'control',
    'other_gap', 'historical_access', 'report_access', 'current_access', 'malformed', 'audit_error',
    'invalid', 'changed_control', 'changed_workspace', 'changed_log_pin', 'stale_usage',
    'recovery_without_capacity', 'missing_workspace_pin'])
def test_unaccounted_refuses_other_causes_before_calls(setup: tuple[Path, Path, Path],
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, case: str) -> None:
    root, _, source = unaccounted_source(setup, monkeypatch, tmp_path)
    report = json.loads((source / 'report.json').read_text())
    state = json.loads((source / 'checkpoint.json').read_text())
    task = report['tasks'][0]
    entry = state['tasks'][task['task_id']]
    runtime = Path(entry['runtime'])
    if case == 'no_marker':
        entry['segments'][0].update(interrupted=False, exit_code=1)
    elif case == 'price_only':
        task['calls'][0]['usage'].update(input_tokens=20, cached_input_tokens=5, output_tokens=8)
    elif case == 'unknown_price':
        task['calls'][0]['usage']['pricing_ref'] = 'not-a-pinned-price'
    elif case == 'unknown_tier':
        entry['segments'][0]['pricing_evidence']['tier'] = 'unknown'
    elif case == 'control':
        task['costs']['control_usd'] = None
    elif case == 'other_gap':
        task['calls'][1]['usage'].update(usd=None, input_tokens=None)
    elif case == 'stale_usage':
        entry['segments'][0]['native_usage'] = {'input_tokens': 20, 'cached_input_tokens': 5, 'output_tokens': 8}
    elif case == 'recovery_without_capacity':
        entry['segments'][0].update(interrupted=False, exit_code=1, infrastructure_recovery=True)
    elif case == 'historical_access':
        entry['result']['grader_access_audit']['matches'] = [{'marker': 'synthetic'}]
    elif case == 'report_access':
        task['grader_access_audit']['matches'] = [{'marker': 'synthetic'}]
    elif case == 'audit_error':
        entry['result']['grader_access_audit']['errors'] = ['unsupported_event:synthetic']
    elif case == 'invalid':
        task['outcome'] = entry['result']['outcome'] = 'invalid'
    elif case == 'changed_control':
        (runtime / 'contract.stdout').write_text('changed')
        entry['control_files'] = {'contract.stdout': '0' * 64}
    elif case == 'changed_workspace':
        (runtime / 'workspace/chunking.py').write_text('changed')
    elif case == 'missing_workspace_pin':
        entry.pop('workspace_exit_sha256')
    elif case == 'changed_log_pin':
        task['executor_segments'][0]['events']['sha256'] = '0' * 64
    else:
        path = runtime / 'exec-1.jsonl'
        path.write_text('broken\n' if case == 'malformed' else json.dumps({'type': 'item.completed',
            'item': {'type': 'command_execution', 'command': 'cat ' + str(root / 'synthetic')}}) + '\n')
    core.write_json(source / 'checkpoint.json', state)
    core.write_json(source / 'report.json', report)

    def forbidden(*args: Any, **kwargs: Any) -> ProcessResult:
        raise AssertionError('No executor, controller, judge or grading call before refusal')

    out = tmp_path / 'refused'
    with pytest.raises((ValueError, core.harness.HarnessError)):
        rerun_unaccounted.rerun_unaccounted(root, source, out, execute=forbidden, version=VERSION)
    assert not out.exists()


def test_regrade_recovers_partial_evidence_without_changing_costs(setup: tuple[Path, Path, Path],
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root, _, source = unaccounted_source(setup, monkeypatch, tmp_path)
    old = json.loads((source / 'report.json').read_text())
    executor = Executor()
    executor.finished = True
    new = json.loads(regrade.regrade(root, source, tmp_path / 'regraded', execute=executor).read_text())
    assert executor.calls == 0 and new['accounting'] == old['accounting']
    assert new['tasks'][0]['costs'] == old['tasks'][0]['costs']
    result = json.loads((tmp_path / 'regraded/bug-chunk-tail/result.json').read_text())
    assert result['segments'][0]['partial_usage']['lower_bound'] is True
    assert 'partial_usage' not in result['segments'][1]
    assert result['executor_runs'][0]['partial_usage'] == result['segments'][0]['partial_usage']
    checkpoint = json.loads((tmp_path / 'regraded/checkpoint.json').read_text())
    assert checkpoint['tasks']['bug-chunk-tail']['segments'][0]['partial_usage']['lower_bound']


def test_unaccounted_cli_conventions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                    capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / 'new'
    monkeypatch.setattr('sys.argv', ['rerun_unaccounted', '--private-root', '/synthetic-unused',
        '--from', 'source', '--out', str(out)])
    observed = []

    def mock(*args: Any, **kwargs: Any) -> Path:
        observed.append((args[-1], kwargs))
        return out / 'report.json'

    monkeypatch.setattr(rerun_invalid, 'rerun_invalid', mock)
    assert rerun_unaccounted.main() == 0
    assert observed == [(set(), {'_unaccounted': True})]
    assert capsys.readouterr().out == str(out) + '\n'


@pytest.mark.parametrize('bounded', [False, True])
def test_host_loss_without_exit_price_capture_needs_native_price_proof(
        setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path, bounded: bool) -> None:
    _, _, source = unaccounted_source(setup, monkeypatch, tmp_path)
    report = json.loads((source / 'report.json').read_text())
    state = json.loads((source / 'checkpoint.json').read_text())
    task = report['tasks'][0]
    entry = state['tasks'][task['task_id']]
    first = entry['segments'][0]
    first.pop('pricing_evidence')
    task['calls'][0]['usage']['pricing_ref'] = None
    native = tmp_path / 'bounded-native.jsonl'
    native.write_text(json.dumps({'type': 'event_msg',
        'timestamp': first['exited_at'] if bounded else entry['segments'][1]['exited_at'],
        'payload': {'type': 'thread_settings_applied', 'thread_settings': {'service_tier': 'standard'}}}) + '\n')
    causes = rerun_invalid.unaccounted_causes(task, entry, entry['result']['grader_access_audit'],
                                            report['metadata']['pricing'], [native])
    assert bool(causes) == bounded
    if bounded:
        assert causes[0]['pricing_evidence']['tier'] == 'standard'
        assert causes[0]['pricing_ref'] is not None
