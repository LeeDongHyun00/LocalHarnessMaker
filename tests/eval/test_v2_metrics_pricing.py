"""Offline calibration, tier accounting and retained final-message regressions."""

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import ValidationError

from eval.metrics import compute
from eval.runner import core
from eval.runner.audit import digest
from eval.runner.compare import compare
from eval.runner.control_accounting import control_calls
from eval.runner.pricing import report_pricing, select
from eval.runner.report import artifact, usage
from eval.runner.schema_compat import report_version, validate_schema
from eval.runner.task_completion import extract, population, publish_summary, retain
from tests.eval.test_control_accounting import generation, retain as retain_control
from tests.eval.test_runner import Executor, setup  # noqa: F401
from tests.eval.test_compare import report as comparison_fixture


@pytest.mark.parametrize('message,claimed', [
    ('Done.', True), ('All requirements completed.', True), ('Implemented the requested feature.', True),
    ('Task implemented; tests passing.', True), ('SC-1 implemented; SC-2 completed.', False),
    ('All tests passing.', False), ('Completed the tests.', False),
    ('Task not completed.', False), ('Task would be completed.', False),
    ('> Task completed.', False), ('```\nTask completed.\n```', False),
    ('Task pending.', False), ('No work completed.', False),
])
def test_task_scope_applies_shared_claim_extractor(message: str, claimed: bool) -> None:
    assert bool(extract(message)) is claimed


def measured_task(tmp_path: Path, task_id: str, message: str | None, outcome: str = 'fail') -> dict[str, Any]:
    directory = tmp_path / task_id
    directory.mkdir()
    (directory / 'exec-1.jsonl').write_text('{"type":"turn.completed"}\n')
    if message is not None:
        (directory / 'final-1.md').write_text(message)
    path = retain(directory, {'segments': [{'attempt': 1, 'events': 'exec-1.jsonl'}]}, two_session=False)
    return {'task_id': task_id, 'task_type': 'bug_fix', 'outcome': outcome, 'attempts': 1, 'two_session': False,
            'done_claims': {'claimed_items': 0, 'claimed_without_evidence': 0},
            'grading': {'result': 'fail' if outcome == 'fail' else 'pass'},
            'costs': {'total_usd': 1}, 'handoff': None, 'artifacts': [artifact(path)]}


def test_task_metric_valid_populations_counts_exclusions_and_seed(tmp_path: Path) -> None:
    tasks = [measured_task(tmp_path, 'pass', 'Task completed.', 'pass'),
             measured_task(tmp_path, 'fail', 'Done.'),
             measured_task(tmp_path, 'invalid', 'Done.', 'invalid'),
             measured_task(tmp_path, 'missing', None)]
    first = compute(tasks, seed=7, resamples=1000)['task_false_done_rate']
    assert first == compute(tasks, seed=7, resamples=1000)['task_false_done_rate']
    assert first['value'] == .5 and first['sample_size'] == 2
    assert first['sample_unit'] == 'claimed_complete_task'
    assert (first['ci95']['lower'], first['ci95']['upper']) == (0, 1)
    _, counts = population(tasks)
    assert (counts['numerator'], counts['denominator']) == (1, 2)
    assert counts['excluded_task_ids'] == ['invalid', 'missing']
    assert 'No retained final' in counts['exclusions']['missing']
    publish_summary(tasks, tmp_path)
    assert json.loads((tmp_path / 'task-completion-summary.json').read_text()) == counts


def test_zero_bootstrap_denominator_is_not_discarded(tmp_path: Path) -> None:
    tasks = [measured_task(tmp_path, 'claim', 'Done.'), measured_task(tmp_path, 'no-claim', 'Still investigating.')]
    value = compute(tasks, seed=0, resamples=1000)['task_false_done_rate']
    assert value['value'] is None and value['sample_size'] == 1
    assert 'bootstrap' in value['undefined_reason']


def test_ungraded_completion_keeps_denominator_and_undefined_outcome(tmp_path: Path) -> None:
    task = measured_task(tmp_path, 'ungraded', 'Done.')
    task['grading'] = None
    _, counts = population([task])
    assert counts['denominator'] == 1 and counts['excluded_task_ids'] == []
    value = compute([task], seed=0, resamples=1000)['task_false_done_rate']
    assert value['value'] is None and value['sample_size'] == 1
    assert 'Hidden grading' in value['undefined_reason']


def test_missing_last_session_never_uses_day_one_or_earlier_final(tmp_path: Path) -> None:
    (tmp_path / 'final-1.md').write_text('Task completed.')
    path = retain(tmp_path, {'segments': [{'attempt': 1, 'day': 1, 'events': 'exec-1.jsonl'}]}, two_session=True)
    assert json.loads(path.read_text())['claimed_complete'] is None
    path = retain(tmp_path, {'segments': [{'attempt': 1, 'day': 1, 'events': 'exec-1.jsonl'},
        {'attempt': 2, 'day': 2, 'events': 'exec-2.jsonl'}]}, two_session=True)
    assert json.loads(path.read_text())['claimed_complete'] is None
    (tmp_path / 'final-2.md').write_text('Work remains pending.')
    path = retain(tmp_path, {'segments': [{'attempt': 2, 'day': 2, 'events': 'exec-2.jsonl'}]}, two_session=True)
    assert json.loads(path.read_text())['claimed_complete'] is False


def test_changed_final_evidence_refused(tmp_path: Path) -> None:
    task = measured_task(tmp_path, 'changed', 'Done.')
    (tmp_path / 'changed/final-1.md').write_text('Still working.')
    with pytest.raises(ValueError, match='Final-message'):
        population([task])


@pytest.mark.parametrize('tier,multiplier', [('standard', 1), ('default', None), ('priority', 2), ('fast', 2), (None, None), ('flex', None)])
def test_call_tier_pricing_and_provenance(tmp_path: Path, tier: str | None, multiplier: int | None) -> None:
    prices = json.loads((core.REPOSITORY / 'eval/prices.yaml').read_text())
    events = tmp_path / 'exec.jsonl'
    events.write_text(json.dumps({'type': 'turn.completed', 'usage': {
        'input_tokens': 1000, 'cached_input_tokens': 200, 'output_tokens': 100}}) + '\n')
    value = usage(events, 1, 'gpt-6-luna', prices, tier=tier)
    assert value['usd'] == (pytest.approx(.000132 * multiplier) if multiplier else None)
    assert bool(value['pricing_ref']) == bool(multiplier)
    entry = {'runtime': str(tmp_path), 'control_files': {}}
    retain_control(entry, 'contract.stderr', generation(service_tier=tier))
    provenance: list[dict[str, Any]] = []
    calls, cost = control_calls(entry, 'synthetic', report_pricing(prices), provenance=provenance)
    assert calls[0]['usage']['usd'] == value['usd'] == cost
    assert provenance[0]['observed_service_tier'] == tier
    assert provenance[0]['pricing_ref'] == value['pricing_ref']
    assert provenance[0]['stderr_sha256'] == entry['control_files']['contract.stderr']


def test_native_tier_required_even_if_requested_or_event_says_priority(tmp_path: Path) -> None:
    from eval.runner.telemetry import collect
    path = tmp_path / 'native.jsonl'
    path.write_text(json.dumps({'type': 'turn_context', 'payload': {'service_tier': 'priority'}}) + '\n')
    assert collect([], [path], '', '')['pricing_evidence']['tier'] == 'unknown'
    prices = json.loads((core.REPOSITORY / 'eval/prices.yaml').read_text())
    assert select(prices, 'gpt-6-luna', None) == (None, None)


def test_calibration_bypasses_freeze_retains_marker_and_compare_refuses(setup: tuple[Path, Path, Path],
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import shutil
    root, path, out = setup
    repository = tmp_path / 'repository'
    shutil.copytree(core.REPOSITORY / 'schemas', repository / 'schemas')
    (repository / 'eval').mkdir(exist_ok=True)
    shutil.copy2(core.REPOSITORY / 'eval/prices.yaml', repository / 'eval/prices.yaml')
    public = repository / 'eval/candidate/bug-chunk-tail'
    shutil.copytree(core.REPOSITORY / 'eval/tasks/bug-chunk-tail', public)
    meta = json.loads((public / 'meta.json').read_text()); meta['frozen'] = False
    (public / 'meta.json').write_text(json.dumps(meta))
    monkeypatch.setattr(core, 'REPOSITORY', repository)
    monkeypatch.setattr(core, 'current_commit', lambda _: 'synthetic')
    monkeypatch.setattr('eval.runner.report.current_commit', lambda _: 'synthetic')
    monkeypatch.setattr(core, 'public_files', lambda task, task_root='eval/tasks': sorted(p for p in public.rglob('*') if p.is_file()))
    config = json.loads(path.read_text()); config['task_root'] = 'eval/candidate'
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='frozen'):
        core.run(path, out, root, execute=Executor(), version=config['codex_version'])
    config['calibration'] = True; path.write_text(json.dumps(config))
    report = json.loads(core.run(path, out, root, execute=Executor(), version=config['codex_version']).read_text())
    assert 'not a headline' in capsys.readouterr().err
    assert json.loads((out / 'checkpoint.json').read_text())['calibration'] is True
    assert json.loads((out / 'run-diagnostics.json').read_text())['calibration'] is True
    with pytest.raises(ValueError, match='calibration'):
        compare(report, report)
    core.run(path, out, root, execute=Executor(), version=config['codex_version'])
    config['calibration'] = False; path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='frozen'):
        core.run(path, out, root, execute=Executor(), version=config['codex_version'])


def test_calibration_config_rejects_nonboolean(setup: tuple[Path, Path, Path]) -> None:
    _, path, _ = setup
    config = json.loads(path.read_text()); config['calibration'] = 'true'
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match='calibration'):
        core.load_config(path)


def test_v1_retained_reports_and_v2_shape_validate_without_migration() -> None:
    for name in ['full-a', 'full-b', 'pilot-a', 'pilot-b', 'smoke-harness-3']:
        path = core.REPOSITORY / 'eval/reports' / name / 'report.json'
        before = path.read_bytes(); report = json.loads(before)
        assert report_version(report) == 1
        validate_schema(report, core.REPOSITORY)
        assert path.read_bytes() == before
        v2 = deepcopy(report)
        v2['metrics']['task_false_done_rate'] = compute([], seed=0, resamples=1000)['task_false_done_rate']
        validate_schema(v2, core.REPOSITORY)
        assert report_version(v2) == 2
        v2['metrics']['task_false_done_rate']['sample_unit'] = 'claimed_criterion'
        with pytest.raises(ValidationError):
            validate_schema(v2, core.REPOSITORY)


def test_compare_v1_v2_uses_shared_metrics_and_both_v2_include_task_rate(tmp_path: Path) -> None:
    left, right = comparison_fixture(), comparison_fixture()
    for report in (left, right):
        report['tasks'] = [measured_task(tmp_path, 'side-'+str(id(report)), 'Task completed.', 'pass')]
        report['tasks'][0]['task_id'] = 'matched'
        report['accounting']['attempted_tasks'] = 1
        report['metrics'] = compute(report['tasks'], seed=0, resamples=1000)
    right['metrics'].pop('task_false_done_rate')
    assert 'task_false_done_rate' not in compare(left, right)['overall']['left']
    right['metrics']['task_false_done_rate'] = left['metrics']['task_false_done_rate']
    result = compare(left, right)
    assert result['overall']['left']['task_false_done_rate']['value'] == 0
    assert result['overall']['paired']['task_false_done_rate_difference']['value'] == 0


def test_native_segment_capture_keeps_mixed_tiers_separate(tmp_path: Path) -> None:
    from eval.runner.telemetry import applied_tier_records, capture_tier
    path = tmp_path / 'native.jsonl'
    def record(tier: str) -> str:
        return json.dumps({'type': 'event_msg', 'payload': {'type': 'thread_settings_applied',
            'thread_settings': {'service_tier': tier}}}) + '\n'
    path.write_text(record('standard'))
    first = capture_tier([path], {})
    before = applied_tier_records([path])
    with path.open('a') as stream:
        stream.write(record('priority'))
    second = capture_tier([path], before)
    assert first['tier'] == 'standard' and second['tier'] == 'priority'
    assert capture_tier([path], applied_tier_records([path]))['tier'] == 'unknown'
    prices = json.loads((core.REPOSITORY / 'eval/prices.yaml').read_text())
    assert select(prices, 'gpt-6-luna', first['tier'])[1] != select(prices, 'gpt-6-luna', second['tier'])[1]


def test_v1_reaudit_and_regrade_use_retained_evidence_only(setup: tuple[Path, Path, Path], tmp_path: Path) -> None:
    from eval.runner import reaudit, regrade
    from eval.runner.process import run_process
    root, path, out = setup
    class FinalExecutor(Executor):
        def __call__(self, argv: list[str], **kwargs: Any) -> Any:
            result = super().__call__(argv, **kwargs)
            if argv[0] == 'codex':
                Path(argv[argv.index('-o') + 1]).write_text('Task completed.')
            return result
    before = json.loads(core.run(path, out, root, execute=FinalExecutor(), version='codex-cli 0.162.0-alpha.17.2').read_text())
    before['metrics'].pop('task_false_done_rate')
    (out / 'report.json').write_text(json.dumps(before))
    state = json.loads((out / 'checkpoint.json').read_text()); state['report_schema'] = 'evaluation-report-v1'
    (out / 'checkpoint.json').write_text(json.dumps(state))
    pinned = (out / 'report.json').read_bytes()
    assert reaudit.reaudit(root, out)[0]['status'] == 'clean'
    def trusted_only(argv: list[str], **kwargs: Any) -> Any:
        assert argv[0] != 'codex' and not any(v in {'controller', 'verifier'} for v in argv)
        return run_process(argv, **kwargs)
    result = json.loads(regrade.regrade(root, out, tmp_path / 'derived', execute=trusted_only).read_text())
    assert result['metrics']['task_false_done_rate']['sample_size'] == 1
    assert result['metrics']['task_false_done_rate']['value'] == 0
    assert result['tasks'][0]['calls'] == before['tasks'][0]['calls']
    assert (out / 'report.json').read_bytes() == pinned


def make_v1_source(source: Path) -> dict[str, Any]:
    """Retain all raw evidence while restoring the original report shape/pins."""
    report = json.loads((source / 'report.json').read_text())
    report['metrics'].pop('task_false_done_rate')
    report['metadata']['pricing'] = {k: v for k, v in json.loads(
        (core.REPOSITORY / 'eval/prices.yaml').read_text()).items() if k != 'snapshots'}
    (source / 'report.json').write_text(json.dumps(report))
    state = json.loads((source / 'checkpoint.json').read_text())
    state['report_schema'] = 'evaluation-report-v1'
    state.pop('pricing_catalog_sha256', None)
    (source / 'checkpoint.json').write_text(json.dumps(state))
    return report


@pytest.mark.parametrize('harness_on', [False, True])
def test_continue_day2_accepts_v1_with_original_price_pins(setup: tuple[Path, Path, Path],
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, harness_on: bool) -> None:
    from eval.runner import continue_day2
    from tests.eval.test_continue_day2 import make_stopped, continuation_executor, VERSION
    root, source, executor = make_stopped(setup, monkeypatch, tmp_path, harness_on=harness_on)
    prior = make_v1_source(source)
    pinned = (source / 'report.json').read_bytes()
    state = json.loads((source / 'checkpoint.json').read_text())
    runtime = Path(state['tasks']['bug-chunk-tail']['runtime'])
    result = json.loads(continue_day2.continue_day2(root, source, tmp_path / 'v1-continued',
        execute=continuation_executor(executor, runtime), version=VERSION).read_text())
    assert result['tasks'][0]['outcome'] == 'pass'
    assert result['tasks'][0]['calls'][:1] == prior['tasks'][0]['calls'][:1]
    assert 'task_false_done_rate' in result['metrics']
    assert (source / 'report.json').read_bytes() == pinned


def test_rerun_invalid_accepts_v1_without_repricing_prior_calls(setup: tuple[Path, Path, Path],
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from eval.runner import rerun_invalid
    from eval.runner.process import run_process
    from tests.eval.test_restart_recovery import infrastructure_source, VERSION
    root, _, source = infrastructure_source(setup, monkeypatch, tmp_path)
    prior = make_v1_source(source)
    pinned = (source / 'report.json').read_bytes()
    executor = Executor()
    def execute(argv: list[str], **kwargs: Any) -> Any:
        return executor(argv, **kwargs) if argv[0] == 'codex' else run_process(argv, **kwargs)
    result = json.loads(rerun_invalid.rerun_invalid(root, source, tmp_path / 'v1-rerun',
        {'execution_interrupted'}, execute=execute, version=VERSION).read_text())
    assert all(t['outcome'] == 'pass' for t in result['tasks']) and executor.calls == 1
    assert 'task_false_done_rate' in result['metrics']
    original_calls = {c['call_id']: c for t in prior['tasks'] for c in t['calls']}
    assert all(c == original_calls[c['call_id']] for t in result['tasks'] for c in t['calls']
               if c['call_id'] in original_calls)
    assert (source / 'report.json').read_bytes() == pinned
