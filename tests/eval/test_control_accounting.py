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
             'reasoning_effort': 'medium', 'pricing_ref': 'controller-price-not-eval',
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
