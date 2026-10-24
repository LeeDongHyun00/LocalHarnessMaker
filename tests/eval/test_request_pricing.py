"""Context bounds apply to native requests, including retained recovery calls."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from eval.metrics import compute
from eval.runner import continue_day2, core, regrade, rerun_invalid, rerun_unaccounted
from eval.runner.control_accounting import control_calls
from eval.runner.pricing import price_usage, retained_provenance, snapshot_hashes
from eval.runner.process import ProcessResult
from eval.runner.report import artifact, usage, validate
from eval.runner.telemetry import native_request_usage, request_usage
from tests.eval.test_control_accounting import generation, retain
from tests.eval.test_continue_day2 import make_stopped, continuation_executor
from tests.eval.test_recovery_pricing import grade_only
from tests.eval.test_restart_recovery import infrastructure_source
from tests.eval.test_runner import Executor, TwoSessionExecutor, setup  # noqa: F401
from tests.eval.test_unaccounted_recovery import unaccounted_source


KEYS = ('input_tokens', 'cached_input_tokens', 'output_tokens')
PRICES = json.loads((core.REPOSITORY / 'eval/prices.yaml').read_text())
VERSION = 'codex-cli 0.162.0-alpha.17.2'


def turns(*, long: bool = False) -> list[dict[str, int]]:
    """Reproduce the supplied totals with twelve independent requests."""
    result = [dict(zip(KEYS, (25000, 24000, 1400))) for _ in range(11)]
    result.append(dict(zip(KEYS, (46619, 44480, 1831))))
    if long:
        result[-1]['input_tokens'] = 272001
    return result


def totals(requests: list[dict[str, int]]) -> dict[str, int]:
    return {k: sum(t[k] for t in requests) for k in KEYS}


def native_events(requests: list[dict[str, int]], *, last: bool = True,
                  duplicates: bool = True) -> list[dict[str, Any]]:
    """Emit native counters and repeated rate-limit observations."""
    events = []
    counts = dict.fromkeys(KEYS, 0)
    for index, turn in enumerate(requests):
        counts = {k: counts[k] + turn[k] for k in KEYS}
        info = {'total_token_usage': dict(counts)}
        if last:
            info['last_token_usage'] = dict(turn, reasoning_output_tokens=123)
        event = {'timestamp': f'2026-10-25T00:00:{index:02d}Z', 'type': 'event_msg',
                 'payload': {'type': 'token_count', 'info': info}}
        events.append(event)
        if duplicates:
            events.append(copy.deepcopy(event))
    return events


def write_events(path: Path, events: list[dict[str, Any]]) -> None:
    path.write_text(''.join(json.dumps(e) + '\n' for e in events))


@pytest.mark.parametrize('last', [False, True])
@pytest.mark.parametrize('long', [False, True])
def test_native_requests_control_context_bound(tmp_path: Path, last: bool, long: bool) -> None:
    requests = turns(long=long)
    native, cli = tmp_path / 'native.jsonl', tmp_path / 'cli.jsonl'
    write_events(native, native_events(requests, last=last))
    write_events(cli, [{'type': 'turn.completed', 'usage': totals(requests)}])
    evidence: dict[str, Any] = {}
    result = usage(cli, 1, 'gpt-6.1-sol', PRICES, tier='priority', native_counts=totals(requests),
                   native_paths=[native], pricing_evidence=evidence)
    assert result['input_tokens'] > 272000
    assert evidence['turn_count'] == 12
    assert evidence['max_input_tokens'] == (272001 if long else 46619)
    assert evidence['context_bound_input_tokens'] == 272000
    assert evidence['exceeded_turn_count'] == int(long)
    if long:
        assert result['usd'] is result['pricing_ref'] is None
        assert evidence['reason'] == 'long_context_rate_missing'
    else:
        assert result['usd'] == pytest.approx(.458872)
        assert result['pricing_ref'] == 'openai-fast-short-2026-10-23-v1'
        assert 'reason' not in evidence


def test_context_bound_comes_from_snapshot_and_is_inclusive() -> None:
    pricing = copy.deepcopy(PRICES)
    pricing['source'] = 'Standard short context up to 10 input tokens'
    evidence: dict[str, Any] = {}
    assert price_usage(dict(zip(KEYS, (10, 0, 0))), pricing, 'gpt-6.1-sol', 'standard',
                       single_request=True, evidence=evidence)[0] is not None
    assert evidence['context_bound_input_tokens'] == 10
    assert price_usage(dict(zip(KEYS, (11, 0, 0))), pricing, 'gpt-6.1-sol', 'standard',
                       single_request=True, evidence=evidence) == (None, None)
    assert evidence['exceeded_turn_count'] == 1


@pytest.mark.parametrize('last', [False, True])
def test_resume_uses_only_new_requests_with_real_previous_total(tmp_path: Path, last: bool) -> None:
    # A prior long request must not poison this short resumed process.
    requests = [dict(zip(KEYS, (300000, 100, 20))), *turns()]
    events = native_events(requests, last=last)
    native = tmp_path / 'native.jsonl'
    write_events(native, events)
    segment = {'started_at': '2026-10-25T00:00:01Z', 'exited_at': '2026-10-25T00:00:12Z'}
    assert native_request_usage([native], totals(turns()), segment=segment) == turns()
    assert native_request_usage([native], totals(turns()),
        before={str(native): (2, requests[0])}) == turns()
    # Without process boundaries the cumulative log cannot establish this delta.
    assert native_request_usage([native], totals(turns())) is None


@pytest.mark.parametrize('case', ['mismatch', 'negative_delta', 'bad_cache', 'missing_counter'])
def test_unproved_native_requests_never_unlock_short_rate(tmp_path: Path, case: str) -> None:
    requests = turns()
    events = native_events(requests, last=False, duplicates=False)
    if case == 'mismatch':
        events.pop()
    elif case == 'negative_delta':
        events[2]['payload']['info']['total_token_usage']['input_tokens'] = 1
    elif case == 'bad_cache':
        events[2]['payload']['info']['total_token_usage']['cached_input_tokens'] = 999999
    else:
        events[-1]['payload']['info'] = {}
    native = tmp_path / 'native.jsonl'
    write_events(native, events)
    assert native_request_usage([native], totals(requests)) is None
    evidence: dict[str, Any] = {}
    assert price_usage(totals(requests), PRICES, 'gpt-6.1-sol', 'priority',
                       evidence=evidence) == (None, None)
    assert evidence['reason'] == 'request_usage_missing'


@pytest.mark.parametrize('long', [False, True])
def test_control_native_requests_use_same_rule(tmp_path: Path, long: bool) -> None:
    requests = turns(long=long)
    envelope = 'control_cli_events ' + json.dumps({'events': ''.join(
        json.dumps(e) + '\n' for e in native_events(requests))}) + '\n'
    entry = {'runtime': str(tmp_path), 'control_files': {}}
    retain(entry, 'contract.stderr', envelope + generation(model='gpt-6.1-sol',
        service_tier='priority', **totals(requests)))
    provenance: list[dict[str, Any]] = []
    calls, cost = control_calls(entry, 'task', PRICES, provenance=provenance)
    assert (cost is None) == long
    assert calls[0]['usage']['usd'] == cost
    evidence = provenance[0]['pricing_evidence']
    assert evidence['turn_count'] == 12 and evidence['exceeded_turn_count'] == int(long)
    if long:
        assert evidence['reason'] == 'long_context_rate_missing'
    else:
        assert cost == pytest.approx(.458872)


def test_http_control_is_one_request_and_never_uses_short_rate_above_bound(tmp_path: Path) -> None:
    entry = {'runtime': str(tmp_path), 'control_files': {}}
    retain(entry, 'contract.stderr', generation(backend='cheap_api', input_tokens=272001))
    rows: list[dict[str, Any]] = []
    calls, cost = control_calls(entry, 'task', PRICES, provenance=rows)
    assert cost is calls[0]['usage']['usd'] is None
    assert rows[0]['pricing_evidence']['turn_count'] == 1
    assert rows[0]['pricing_evidence']['reason'] == 'long_context_rate_missing'


class NativeExecutor(Executor):
    """Mock model work and append real-shaped native per-request counters."""

    def __init__(self, *, long: bool = False) -> None:
        super().__init__()
        self.requests = turns(long=long)

    def __call__(self, argv: list[str], **kwargs: Any) -> ProcessResult:
        result = super().__call__(argv, **kwargs)
        if argv[0] == 'codex':
            native = Path(kwargs['env']['CODEX_HOME']) / 'sessions/rollout-unit.jsonl'
            events = [json.loads(line) for line in native.read_text().splitlines()]
            for event in events:
                if event.get('payload', {}).get('type') == 'thread_settings_applied':
                    event['payload']['thread_settings']['service_tier'] = 'priority'
            # Historical requests have no timestamps: totals must match exactly.
            counts = native_events(self.requests)
            for event in counts:
                event.pop('timestamp')
            write_events(native, events + counts)
        return result


@pytest.mark.parametrize('operation', ['invalid', 'unaccounted'])
@pytest.mark.parametrize('long', [False, True])
def test_recovery_reruns_price_fresh_native_requests(setup: tuple[Path, Path, Path],
        monkeypatch: pytest.MonkeyPatch, tmp_path: Path, operation: str, long: bool) -> None:
    create = infrastructure_source if operation == 'invalid' else unaccounted_source
    root, _, source = create(setup, monkeypatch, tmp_path)
    executor = NativeExecutor(long=long)

    def mocked(argv: list[str], **kwargs: Any) -> ProcessResult:
        return executor(argv, **kwargs) if argv[0] == 'codex' else grade_only(argv, **kwargs)

    out = tmp_path / 'rerun'
    options = dict(execute=mocked, version=VERSION)
    path = (rerun_invalid.rerun_invalid(root, source, out, {'execution_interrupted'}, **options)
            if operation == 'invalid' else rerun_unaccounted.rerun_unaccounted(root, source, out, **options))
    report = json.loads(path.read_text())
    task = next(t for t in report['tasks'] if t['task_id'] == 'bug-chunk-tail')
    call = task['calls'][-1]
    assert executor.calls == 1 and (call['usage']['usd'] is None) == long
    evidence = retained_provenance(task)[-1]['pricing_evidence']
    assert evidence['turn_count'] == 12 and evidence['exceeded_turn_count'] == int(long)
    if long:
        assert evidence['reason'] == 'long_context_rate_missing'
    else:
        assert call['usage']['usd'] == pytest.approx(.458872)


def test_continuation_recovers_old_null_and_prices_new_native_requests(
        setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    original = TwoSessionExecutor.__call__

    def mocked(self: TwoSessionExecutor, argv: list[str], **kwargs: Any) -> ProcessResult:
        result = original(self, argv, **kwargs)
        if argv[0] == 'codex':
            native = Path(kwargs['env']['CODEX_HOME']) / f'sessions/rollout-day-{self.calls}.jsonl'
            events = [json.loads(line) for line in native.read_text().splitlines()]
            for event in events:
                if event.get('payload', {}).get('type') == 'thread_settings_applied':
                    event['payload']['thread_settings']['service_tier'] = 'priority'
            counts = native_events(turns())
            for event in counts:
                event.pop('timestamp')
            write_events(native, events + counts)
        return result

    monkeypatch.setattr(TwoSessionExecutor, '__call__', mocked)
    root, source, executor = make_stopped(setup, monkeypatch, tmp_path, harness_on=False)
    report = json.loads((source / 'report.json').read_text())
    old = report['tasks'][0]
    old['calls'][0]['usage'].update(usd=None, pricing_ref=None)
    old['costs'].update(executor_usd=None, total_usd=None)
    ref = next(a for a in old['artifacts'] if Path(a['path']).name == 'pricing-provenance.json')
    rows = retained_provenance(old)
    rows[0].update(pricing_ref=None, pricing_snapshot_sha256=None)
    core.write_json(Path(ref['path']), rows)
    ref.update(artifact(Path(ref['path'])))
    report['accounting']['total_cost_usd'] = None
    report['metrics'] = compute(report['tasks'], seed=report['metadata']['confidence']['seed'], resamples=10000)
    core.write_json(source / 'report.json', report)
    state = json.loads((source / 'checkpoint.json').read_text())
    runtime = Path(state['tasks'][old['task_id']]['runtime'])
    result = json.loads(continue_day2.continue_day2(root, source, tmp_path / 'continued',
        execute=continuation_executor(executor, runtime), version=VERSION).read_text())
    task = result['tasks'][0]
    assert [c['usage']['usd'] for c in task['calls']] == pytest.approx([.458872, .458872])
    assert task['costs']['executor_usd'] == pytest.approx(.917744)
    assert retained_provenance(task)[0]['repricing']['previous_usage']['usd'] is None


def test_invalid_rerun_recovers_null_historical_spending_before_retaining_it(
        setup: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import tests.eval.test_restart_recovery as recovery
    monkeypatch.setattr(recovery, 'Executor', NativeExecutor)
    root, _, source = infrastructure_source(setup, monkeypatch, tmp_path)
    report = json.loads((source / 'report.json').read_text())
    task = next(t for t in report['tasks'] if t['task_id'] == 'bug-chunk-tail')
    task['calls'][0]['usage'].update(usd=None, pricing_ref=None)
    task['costs'].update(executor_usd=None, total_usd=None)
    ref = next(a for a in task['artifacts'] if Path(a['path']).name == 'pricing-provenance.json')
    rows = retained_provenance(task)
    rows[0].update(pricing_ref=None, pricing_snapshot_sha256=None)
    core.write_json(Path(ref['path']), rows)
    ref.update(artifact(Path(ref['path'])))
    report['accounting']['total_cost_usd'] = None
    report['metrics'] = compute(report['tasks'], seed=report['metadata']['confidence']['seed'], resamples=10000)
    core.write_json(source / 'report.json', report)
    executor = NativeExecutor()

    def mocked(argv: list[str], **kwargs: Any) -> ProcessResult:
        return executor(argv, **kwargs) if argv[0] == 'codex' else grade_only(argv, **kwargs)

    updated = json.loads(rerun_invalid.rerun_invalid(root, source, tmp_path / 'retained-rerun',
        {'execution_interrupted'}, execute=mocked, version=VERSION).read_text())
    task = next(t for t in updated['tasks'] if t['task_id'] == 'bug-chunk-tail')
    assert [c['usage']['usd'] for c in task['calls']] == pytest.approx([.458872, .458872])
    assert retained_provenance(task)[0]['repricing']['previous_usage']['usd'] is None


@pytest.mark.parametrize('long', [False, True])
def test_run_and_regrade_reprice_null_history_without_changing_pins(
        setup: tuple[Path, Path, Path], tmp_path: Path, long: bool) -> None:
    root, config, source = setup
    report = json.loads(core.run(config, source, root, execute=NativeExecutor(long=long), version=VERSION).read_text())
    task = report['tasks'][0]
    assert (task['calls'][0]['usage']['usd'] is None) == long
    assert retained_provenance(task)[0]['pricing_evidence']['turn_count'] == 12
    # Simulate the old session-level guard and historical provenance. Keep the
    # already-priced Standard call alongside the formerly-null Fast call.
    task['calls'][0]['usage'].update(usd=None, pricing_ref=None)
    historical = copy.deepcopy(task['calls'][0])
    historical['call_id'] = 'historical-standard'
    historical['purpose'] = 'contract'
    historical['usage'].update(input_tokens=20, cached_input_tokens=5, output_tokens=8,
                               usd=.0001105, pricing_ref=PRICES['snapshot_id'])
    task['calls'].append(historical)
    task['costs'] = {'executor_usd': None, 'control_usd': .0001105, 'total_usd': None}
    ref = next(a for a in task['artifacts'] if Path(a['path']).name == 'pricing-provenance.json')
    prior_rows = [dict(retained_provenance(task)[0], pricing_ref=None, pricing_snapshot_sha256=None),
                  {'call_id': historical['call_id'], 'pricing_ref': PRICES['snapshot_id'],
                   'basis': 'Original Standard accounting',
                   'pricing_snapshot_sha256': snapshot_hashes(PRICES)[PRICES['snapshot_id']]}]
    prior_rows[0].pop('pricing_evidence')
    core.write_json(Path(ref['path']), prior_rows)
    ref.update(artifact(Path(ref['path'])))
    report['accounting']['total_cost_usd'] = None
    report['metrics'] = compute(report['tasks'], seed=report['metadata']['confidence']['seed'], resamples=10000)
    core.write_json(source / 'report.json', report)
    state = json.loads((source / 'checkpoint.json').read_text())
    entry = state['tasks'][task['task_id']]
    for segment in entry['segments'] + entry['result']['segments']:
        segment.pop('native_request_usage', None)
    core.write_json(source / 'checkpoint.json', state)
    validate(report, core.REPOSITORY)
    source_bytes = {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()}
    out = tmp_path / 'regraded'
    updated = json.loads(regrade.regrade(root, source, out, execute=grade_only).read_text())
    new_task = updated['tasks'][0]
    assert new_task['calls'][1] == historical
    assert updated['metadata']['pricing'] == report['metadata']['pricing']
    rows = retained_provenance(new_task, updated['metadata']['pricing'])
    evidence = rows[0]['pricing_evidence']
    assert evidence['turn_count'] == 12
    if long:
        assert new_task['calls'][0]['usage']['usd'] is None
        assert evidence['reason'] == 'long_context_rate_missing'
    else:
        assert new_task['calls'][0]['usage']['usd'] == pytest.approx(.458872)
        assert updated['metrics']['cost_per_pass']['value'] == pytest.approx(.4589825)
        assert rows[0]['repricing']['previous_usage']['usd'] is None
        assert rows[0]['repricing']['previous_provenance'] == prior_rows[0]
        assert rows[0]['pricing_snapshot_sha256'] == snapshot_hashes(PRICES)[rows[0]['pricing_ref']]
    assert rows[1] == prior_rows[1]
    again = json.loads(regrade.regrade(root, out, tmp_path / 'again', execute=grade_only).read_text())
    assert again['tasks'][0]['calls'] == new_task['calls']
    assert again['accounting'] == updated['accounting']
    assert source_bytes == {p.relative_to(source): p.read_bytes() for p in source.rglob('*') if p.is_file()}


def test_rate_limit_only_updates_do_not_create_requests() -> None:
    events = native_events(turns())
    events.append({'type': 'event_msg', 'payload': {'type': 'token_count', 'info': None}})
    assert request_usage(events) == turns()
