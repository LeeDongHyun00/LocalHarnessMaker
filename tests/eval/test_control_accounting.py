"""Control stderr accounting uses exact controller and delegated judge envelopes."""

import json
from pathlib import Path
from typing import Any

import pytest

from eval.runner.audit import digest
from eval.runner.control_accounting import control_calls
from eval.runner.core import REPOSITORY, load_config, paid_call_bound, require_call_estimate


PRICES = json.loads((REPOSITORY / 'eval/prices.yaml').read_text())


def generation(**overrides: Any) -> str:
    value = {'backend': 'codex_cli', 'model': 'gpt-6-luna', 'status': 'success',
             'reasoning_effort': 'medium', 'service_tier': 'standard', 'pricing_ref': 'controller-price-not-eval',
             'input_tokens': 1000, 'cached_input_tokens': 200, 'output_tokens': 100,
             'usd': 999, 'latency_seconds': .25}
    value.update(overrides)
    return 'control_call ' + json.dumps(value, sort_keys=True) + '\n'


def delegation(complete: bool = True, count: int = 1, outcome: str = 'completed') -> str:
    return 'judge_delegation ' + json.dumps({'accounting_complete': complete, 'backend': 'codex_cli',
        'criterion_id': 'SC-1', 'forwarded_control_calls': count, 'outcome': outcome},
        sort_keys=True, separators=(',', ':')) + '\n'


def retain(entry: dict[str, Any], name: str, text: str, *, code: int | None = 0,
           timed_out: bool = False) -> None:
    path = Path(entry['runtime']) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    entry['control_files'][name] = digest(path.read_bytes())
    manifest = path.with_suffix('.control.json')
    manifest.write_text(json.dumps({'exit_code': code, 'timed_out': timed_out}))
    entry['control_files'][str(manifest.relative_to(entry['runtime']))] = digest(manifest.read_bytes())


@pytest.fixture
def entry(tmp_path: Path) -> dict[str, Any]:
    return {'runtime': str(tmp_path), 'control_files': {}}


def test_contract_fallback_and_forwarded_judge_calls(entry: dict[str, Any]) -> None:
    retain(entry, 'contract.stderr', generation(status='error') + generation(backend='cheap_api'))
    retain(entry, 'verdict-1.stderr', 'control_cli_events {"events":""}\n' + generation() + delegation())
    calls, usd = control_calls(entry, 'task', PRICES)
    assert [c['purpose'] for c in calls] == ['contract', 'contract', 'judge']
    assert [c['backend'] for c in calls] == ['codex_cli', 'cheap_api', 'codex_cli']
    assert [c['status'] for c in calls] == ['failed', 'completed', 'completed']
    assert usd == pytest.approx(3 * .000132)
    assert all(c['usage']['pricing_ref'] == PRICES['snapshot_id'] for c in calls)
    assert all(c['usage']['latency_seconds'] == .25 for c in calls)


@pytest.mark.parametrize('case', ['judge_incomplete', 'contract_no_success', 'handoff_no_success',
    'timeout', 'failed_empty', 'interrupted', 'unknown_model', 'missing_model', 'missing_input',
    'missing_cache', 'missing_output', 'bad_cache', 'malformed', 'missing_stream', 'missing_manifest',
    'judge_count_mismatch', 'judge_missing_delegation', 'bad_hash'])
def test_missing_accounting_propagates_null(entry: dict[str, Any], case: str) -> None:
    text, name, code, timed_out = generation(), 'contract.stderr', 0, False
    if case == 'judge_incomplete':
        name, text = 'verdict-1.stderr', generation() + delegation(False, outcome='failed')
    elif case in {'contract_no_success', 'handoff_no_success'}:
        name, text = ('handoff.stderr' if case.startswith('handoff') else name), generation(status='error')
    elif case == 'timeout':
        timed_out = True
    elif case == 'failed_empty':
        text, code = '', 2
    elif case == 'interrupted':
        code = None
    elif case == 'unknown_model':
        text = generation(model='unpriced')
    elif case == 'missing_model':
        text = generation(model=None)
    elif case.startswith('missing_') and case.split('_')[1] in {'input', 'cache', 'output'}:
        field = {'input': 'input_tokens', 'cache': 'cached_input_tokens', 'output': 'output_tokens'}[case.split('_')[1]]
        text = generation(**{field: None})
    elif case == 'bad_cache':
        text = generation(cached_input_tokens=1001)
    elif case == 'malformed':
        text += 'control_call {truncated\n'
    elif case == 'judge_missing_delegation':
        name = 'verdict-1.stderr'
    elif case == 'judge_count_mismatch':
        name, text = 'verdict-1.stderr', generation() + delegation(count=2)
    retain(entry, name, text, code=code, timed_out=timed_out)
    if case == 'missing_stream':
        entry['control_files'].pop(name)
    elif case == 'missing_manifest':
        entry['control_files'].pop('contract.control.json')
    elif case == 'bad_hash':
        (Path(entry['runtime']) / name).write_text('changed')
    calls, usd = control_calls(entry, 'task', PRICES)
    assert usd is None
    if case == 'timeout':
        assert calls[0]['status'] == 'timeout'


def test_archived_calls_and_zero_call_mechanical_verifier(entry: dict[str, Any]) -> None:
    retain(entry, 'control-interruptions/one/contract.stderr', generation(status='error'), code=2)
    retain(entry, 'contract.stderr', generation())
    retain(entry, 'verdict-1.stderr', '')
    calls, usd = control_calls(entry, 'task', PRICES)
    assert len(calls) == 2 and len({c['call_id'] for c in calls}) == 2
    assert usd == pytest.approx(2 * .000132)


def test_new_config_estimates_match_and_changed_config_stops() -> None:
    smoke = load_config(REPOSITORY / 'eval/configs/smoke-harness.yaml')
    full = load_config(REPOSITORY / 'eval/configs/full-harness.yaml')
    assert paid_call_bound(smoke) == 21 and paid_call_bound(full) == 900
    assert paid_call_bound(smoke, {'day1': 1, 'day2': 2}) == 48
    assert full['tasks'] == load_config(REPOSITORY / 'eval/configs/full-a.yaml')['tasks']
    assert smoke['reinstruction_limit'] == full['reinstruction_limit'] == 2
    with pytest.raises(ValueError, match='STOP-3'):
        require_call_estimate({**full, 'seed': 99})


def test_embedded_markers_are_not_records(entry: dict[str, Any]) -> None:
    retain(entry, 'contract.stderr', generation() +
           'control_cli_events ' + json.dumps({'event': 'control_call {broken judge_delegation {'}) + '\n')
    calls, usd = control_calls(entry, 'task', PRICES)
    assert len(calls) == 1
    assert usd == pytest.approx(.000132)


@pytest.mark.parametrize('mode,expected', [('all_judge', 0), ('budget', 0), ('missing', None),
                                         ('wrong_evidence', None), ('not_unverifiable', None),
                                         ('partial_budget', None), ('bad_hash', None)])
def test_zero_judge_delegations(entry: dict[str, Any], mode: str, expected: float | None) -> None:
    root = Path(entry['runtime'])
    criteria = [{'id': 'J1', 'check': {'type': 'llm_judge'}},
                {'id': 'J2', 'check': {'type': 'llm_judge'}}]
    if mode != 'all_judge':
        criteria.append({'id': 'M', 'check': {'type': 'file_exists'}})
    contract = root / 'contract.json'
    contract.write_text(json.dumps({'success_criteria': criteria}))
    entry['control_files']['contract.json'] = digest(contract.read_bytes())
    retain(entry, 'verdict-1.stderr', '')
    if mode != 'missing':
        verdict = root / 'verdict-1.json'
        items = [{'id': c['id'], 'status': 'unverifiable',
                  'evidence': 'criterion not started: HARNESS_VERIFY_BUDGET_SECONDS exhausted'}
                 for c in criteria]
        if mode in {'wrong_evidence', 'partial_budget'}:
            items[0]['evidence'] = 'judge failed'
        if mode == 'not_unverifiable':
            items[0]['status'] = 'pass'
        verdict.write_text(json.dumps({'items': items}))
        entry['control_files']['verdict-1.json'] = digest(verdict.read_bytes())
        if mode == 'bad_hash':
            verdict.write_text('{}')
    assert control_calls(entry, 'task', PRICES) == ([], expected)


@pytest.mark.parametrize('items', [False, True])
@pytest.mark.parametrize('logged_call', [False, True])
def test_capacity_refusal_usage_from_envelope(entry: dict[str, Any], items: bool, logged_call: bool) -> None:
    message = 'Selected model is at capacity. Please try a different model.'
    events = ([{'type': 'item.started', 'item': {'type': 'reasoning'}}] if items else []) + [
        {'type': 'error', 'message': message},
        {'type': 'turn.failed', 'error': {'message': message}},
    ]
    text = 'control_cli_events ' + json.dumps({'model': 'gpt-6-luna',
        'events': ''.join(json.dumps(e) + '\n' for e in events)}) + '\n'
    if logged_call:
        text += generation(status='error', input_tokens=None, cached_input_tokens=None, output_tokens=None)
    retain(entry, 'control-interruptions/one/contract.stderr', text, code=2)
    calls, cost = control_calls(entry, 'task', PRICES)
    assert len(calls) == 1
    expected = None if items else 0
    assert cost == expected and calls[0]['usage']['usd'] == expected
    assert calls[0]['usage']['input_tokens'] == (None if items else 0)
    assert calls[0]['usage']['cached_input_tokens'] == (None if items else 0)
    assert calls[0]['usage']['output_tokens'] == (None if items else 0)


def test_capacity_does_not_zero_previous_success_or_http_fallback(entry: dict[str, Any]) -> None:
    message = 'Selected model is at capacity. Please try a different model.'
    CAPACITY_STREAM = json.dumps({'type': 'error', 'message': message}) + '\n'
    envelope = 'control_cli_events ' + json.dumps({'model': 'gpt-6-luna', 'events': CAPACITY_STREAM}) + '\n'
    retain(entry, 'contract.stderr', generation() + envelope +
           generation(status='error', input_tokens=None, cached_input_tokens=None, output_tokens=None) +
           generation(backend='cheap_api'))
    calls, cost = control_calls(entry, 'task', PRICES)
    assert [c['usage']['input_tokens'] for c in calls] == [1000, 0, 1000]
    assert cost == pytest.approx(2 * .000132)


def test_runtime_below_symlinked_parent_retains_control_costs(tmp_path: Path) -> None:
    actual = tmp_path / 'actual'
    actual.mkdir()
    alias = tmp_path / 'alias'
    alias.symlink_to(actual, target_is_directory=True)
    entry = {'runtime': str(alias / 'runtime'), 'control_files': {}}
    retain(entry, 'contract.stderr', generation())
    calls, usd = control_calls(entry, 'task', PRICES)
    assert [call['model'] for call in calls] == ['gpt-6-luna']
    assert usd == pytest.approx(.000132)


@pytest.mark.parametrize('location', ['runtime', 'child', 'file', 'traversal', 'absolute'])
def test_control_accounting_rejects_links_within_runtime_and_escapes(tmp_path: Path, location: str) -> None:
    runtime = tmp_path / 'runtime'
    entry = {'runtime': str(runtime), 'control_files': {}}
    retain(entry, 'child/contract.stderr', generation())
    target = tmp_path / 'retained'
    if location == 'runtime':
        runtime.rename(target)
        runtime.symlink_to(target, target_is_directory=True)
    elif location == 'child':
        (runtime / 'child').rename(target)
        (runtime / 'child').symlink_to(target, target_is_directory=True)
    elif location == 'file':
        (runtime / 'child/contract.stderr').rename(target)
        (runtime / 'child/contract.stderr').symlink_to(target)
    else:
        entry['control_files'] = {
            str(runtime / name) if location == 'absolute' else '../runtime/' + name: value
            for name, value in entry['control_files'].items()}
    assert control_calls(entry, 'task', PRICES) == ([], None)


@pytest.mark.parametrize('logged_call', [False, True])
def test_unicode_separators_inside_control_jsonl_values(entry: dict[str, Any], logged_call: bool) -> None:
    events = json.dumps({'type': 'error', 'message': 'NEL\u0085LS\u2028PS\u2029 at capacity'},
                        ensure_ascii=False) + '\n'
    text = 'control_cli_events ' + json.dumps({'model': 'gpt-6-luna', 'events': events}, ensure_ascii=False) + '\n'
    if logged_call:
        text += generation(status='error', input_tokens=None, cached_input_tokens=None, output_tokens=None)
    retain(entry, 'control-interruptions/unicode/contract.stderr', text, code=2)
    calls, cost = control_calls(entry, 'task', PRICES)
    assert len(calls) == 1 and cost == 0
    assert calls[0]['usage']['input_tokens'] == 0
