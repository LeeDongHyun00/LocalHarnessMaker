"""Mocked recoveries pin fresh controls and retain mixed-snapshot provenance."""

import copy
import json
from pathlib import Path
from typing import Any, Callable

import pytest

from eval.runner import continue_day2, core, regrade, rerun_invalid, rerun_unaccounted
from eval.runner.audit import digest
from eval.runner.control_accounting import control_calls
from eval.runner.pricing import retained_provenance, snapshot_hashes
from eval.runner.process import ProcessResult, run_process
from eval.runner.report import artifact, validate
from tests.eval.test_control_accounting import delegation, generation, retain
from tests.eval.test_continue_day2 import continuation_executor, make_stopped
from tests.eval.test_restart_recovery import VERSION, infrastructure_source
from tests.eval.test_runner import Executor, TwoSessionExecutor, setup  # noqa: F401
from tests.eval.test_unaccounted_recovery import unaccounted_source
from tests.eval.test_v2_metrics_pricing import make_v1_source


def accounting(execute: Callable[..., ProcessResult]) -> Callable[..., ProcessResult]:
    """Supply real-shaped control logs after a fully mocked CLI producer."""
    def wrapped(argv: list[str], **kwargs: Any) -> ProcessResult:
        result = execute(argv, **kwargs)
        if '-m' in argv and argv[argv.index('-m') + 1] in {'controller', 'verifier'}:
            operation = argv[argv.index('-m') + 2]
            if operation != 'validate-handoff':
                # Host control_call records omit this field entirely.
                record = json.loads(generation().removeprefix('control_call '))
                record.pop('service_tier')
                line = 'control_call ' + json.dumps(record) + '\n'
                kwargs['stderr'].write_text(
                    line.replace('"success"', '"error"') + line if operation == 'contract'
                    else line + delegation() if operation == 'check' else line)
        return result
    return wrapped


def grade_only(argv: list[str], **kwargs: Any) -> ProcessResult:
    """Run synthetic private tests and forbid every model transport."""
    assert argv[0] != 'codex' and not any(value in {'controller', 'verifier'} for value in argv)
    return run_process(argv, **kwargs)


@pytest.mark.parametrize('model,expected', [('gpt-6.1-sol', 'standard'), ('gpt-6-luna', 'priority'),
                                          ('unknown-model', 'unknown')])
@pytest.mark.parametrize('tier', ['omitted', None, 'standard', 'priority', 'default', 'flex'])
def test_control_tier_uses_record_then_model_default(tmp_path: Path, model: str,
        expected: str, tier: str | None) -> None:
    prices = json.loads((core.REPOSITORY / 'eval/prices.yaml').read_text())
    record = json.loads(generation(model=model, service_tier=tier).removeprefix('control_call '))
    if tier == 'omitted':
        record.pop('service_tier')
    entry = {'runtime': str(tmp_path), 'control_files': {}}
    retain(entry, 'contract.stderr', 'control_call ' + json.dumps(record) + '\n')
    rows: list[dict[str, Any]] = []
    calls, cost = control_calls(entry, 'task', prices, provenance=rows)
    selected = expected if tier in {None, 'omitted'} else 'standard' if tier == 'default' else tier
    assert rows[0]['pricing_evidence']['tier'] == selected
    assert ('inferred from the model default' in rows[0]['basis']) == (
        tier in {None, 'omitted'} and expected != 'unknown')
    assert (cost is not None) == (selected in {'standard', 'priority'} and model != 'unknown-model')
    assert calls[0]['usage']['usd'] == cost


@pytest.mark.parametrize('operation', ['invalid', 'unaccounted'])
def test_v1_task_rerun_then_regrade_with_mixed_snapshots(setup: tuple[Path, Path, Path],
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, operation: str) -> None:
    create = infrastructure_source if operation == 'invalid' else unaccounted_source
    root, config_path, source = create(setup, monkeypatch, tmp_path)
    state = json.loads((source / 'checkpoint.json').read_text())
    config = state['config']
    config.update(harness=True, control_backend='codex_cli', reinstruction_limit=0)
    core.write_json(config_path, config)
    state['config_sha256'] = digest(config_path.read_bytes())
    core.write_json(source / 'checkpoint.json', state)
    prior = make_v1_source(source)
    prior['metadata']['config_sha256'] = state['config_sha256']
    prior['metadata']['control_backend'] = config['control_backend']
    # A retained v1 observation must survive the normal runner's report build.
    for task in prior['tasks']:
        ref = next(a for a in task['artifacts'] if Path(a['path']).name == 'pricing-provenance.json')
        path = Path(ref['path'])
        rows = json.loads(path.read_text())
        for row in rows:
            row['basis'] = 'Retained version 1 accounting; no tier observation.'
            row.pop('pricing_snapshot_sha256', None)
        core.write_json(path, rows)
        ref.update(artifact(path))
    core.write_json(source / 'report.json', prior)
    source_bytes = {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()}
    controls, executor = TwoSessionExecutor(), Executor()

    def mocked(argv: list[str], **kwargs: Any) -> ProcessResult:
        if '-m' in argv and argv[argv.index('-m') + 1] in {'controller', 'verifier'}:
            result = controls(argv, **kwargs)
            if argv[argv.index('-m') + 1] == 'verifier':
                path = Path(argv[argv.index('--out') + 1])
                value = json.loads(path.read_text())
                value.update(overall='pass', reinstruct_message=None)
                value['items'][0]['status'] = 'pass'
                path.write_text(json.dumps(value))
            return result
        return executor(argv, **kwargs) if argv[0] == 'codex' else grade_only(argv, **kwargs)

    out = tmp_path / 'mixed-rerun'
    options = dict(execute=accounting(mocked), version=VERSION)
    result_path = (rerun_invalid.rerun_invalid(root, source, out, {'execution_interrupted'}, **options)
                   if operation == 'invalid' else rerun_unaccounted.rerun_unaccounted(root, source, out, **options))
    report = json.loads(result_path.read_text())
    fresh = next(t for t in report['tasks'] if t['task_id'] == 'bug-chunk-tail')
    other = next(t for t in report['tasks'] if t['task_id'] != 'bug-chunk-tail')
    assert executor.calls == 1 and all(t['outcome'] == 'pass' for t in report['tasks'])
    control = [c for c in fresh['calls'] if c['purpose'] != 'executor']
    assert [c['purpose'] for c in control] == ['contract', 'contract', 'judge']
    assert fresh['costs']['control_usd'] == pytest.approx(3 * .000264)
    assert report['metrics']['cost_per_pass']['value'] is not None
    old_other = next(t for t in prior['tasks'] if t['task_id'] == other['task_id'])
    assert other['calls'] == old_other['calls'] and other['costs'] == old_other['costs']
    assert retained_provenance(other)[0]['basis'] == 'Retained version 1 accounting; no tier observation.'
    entry = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    for name in ('contract.stderr', 'verdict-1.stderr'):
        assert entry['control_files'][name] == digest((Path(entry['runtime']) / name).read_bytes())
    pins = snapshot_hashes(report['metadata']['pricing'])
    rows = retained_provenance(fresh, report['metadata']['pricing'])
    assert len({c['usage']['pricing_ref'] for t in report['tasks'] for c in t['calls']}) == 2
    assert all(row['pricing_snapshot_sha256'] == pins[row['pricing_ref']] for row in rows)
    before = copy.deepcopy(report)
    def forbidden(argv: list[str], **kwargs: Any) -> ProcessResult:
        raise AssertionError('Completed checkpoint must not call any external process')
    resumed = json.loads(core.run(out / 'rerun-config.yaml', out, root, execute=forbidden,
        version=VERSION, _recorded_config_sha256=state['config_sha256']).read_text())
    assert resumed['accounting'] == before['accounting']
    assert [t['calls'] for t in resumed['tasks']] == [t['calls'] for t in before['tasks']]
    for index in range(2):
        dest = tmp_path / f'regraded-{index}'
        report = json.loads(regrade.regrade(root, out, dest, execute=grade_only).read_text())
        assert report['accounting'] == before['accounting']
        assert [t['calls'] for t in report['tasks']] == [t['calls'] for t in before['tasks']]
        validate(report, core.REPOSITORY)
        out = dest
    assert source_bytes == {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()}


def test_continued_day2_prices_new_pinned_control_streams(setup: tuple[Path, Path, Path],
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    root, source, executor = make_stopped(setup, monkeypatch, tmp_path, harness_on=True)
    entry = json.loads((source / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    out = tmp_path / 'continued-priced'
    report = json.loads(continue_day2.continue_day2(root, source, out,
        execute=accounting(continuation_executor(executor, Path(entry['runtime']))), version=VERSION).read_text())
    task = report['tasks'][0]
    fresh = [c for c in task['calls'] if '-continuation-control-' in c['call_id']]
    assert sorted(c['purpose'] for c in fresh) == ['contract', 'contract', 'handoff', 'judge', 'judge']
    assert all(c['usage']['usd'] == pytest.approx(.000264) for c in fresh)
    assert all('fast' in c['usage']['pricing_ref'] for c in fresh)
    rows = retained_provenance(task, report['metadata']['pricing'])
    assert all('inferred from the model default' in row['basis'] for row in rows
               if '-continuation-control-' in row['call_id'])
    entry = json.loads((out / 'checkpoint.json').read_text())['tasks']['bug-chunk-tail']
    for name in ('day-2/contract.stderr', 'day-2/verdict-1.stderr', 'handoff.stderr'):
        assert entry['control_files'][name] == digest((Path(entry['runtime']) / name).read_bytes())
    graded = json.loads(regrade.regrade(root, out, tmp_path / 'continued-regraded', execute=grade_only).read_text())
    assert graded['tasks'][0]['calls'] == task['calls']


@pytest.mark.parametrize('case', ['snapshot_bytes', 'snapshot_pin', 'artifact_bytes', 'missing_reference'])
def test_pricing_provenance_still_rejects_tampering(setup: tuple[Path, Path, Path], case: str) -> None:
    root, config, out = setup
    report = json.loads(core.run(config, out, root, execute=Executor(), version=VERSION).read_text())
    task = report['tasks'][0]
    ref = next(a for a in task['artifacts'] if Path(a['path']).name == 'pricing-provenance.json')
    path = Path(ref['path'])
    if case == 'snapshot_bytes':
        pricing = report['metadata']['pricing']
        catalog = json.loads(pricing['source'].removeprefix('Pinned tier snapshots: '))
        catalog[0]['rates'][0]['input_per_million_usd'] += 1
        pricing['source'] = 'Pinned tier snapshots: ' + json.dumps(catalog)
    elif case == 'missing_reference':
        task['calls'][0]['usage']['pricing_ref'] = 'missing-snapshot'
    else:
        rows = json.loads(path.read_text())
        rows[0]['pricing_snapshot_sha256'] = '0' * 64
        core.write_json(path, rows)
        if case == 'snapshot_pin':
            ref.update(artifact(path))
    with pytest.raises(ValueError, match='Pricing .*hash mismatch|Call pricing snapshot unavailable'):
        validate(report, core.REPOSITORY)
