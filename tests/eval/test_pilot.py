"""Frozen pilot selection and the user-supplied price snapshot."""

from collections import Counter
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from eval.metrics import compute, total
from eval.runner.core import REPOSITORY, load_config
from eval.runner.report import usage


def test_pilot_configs_use_same_frozen_deterministic_strata() -> None:
    configs = [load_config(REPOSITORY / f'eval/configs/pilot-{b}.yaml') for b in ('a', 'b')]
    a, b = configs
    assert a['reasoning_effort'] == 'medium'
    assert b['reasoning_effort'] == 'max'
    assert {k: v for k, v in a.items() if k not in {'name', 'reasoning_effort'}} == {
        k: v for k, v in b.items() if k not in {'name', 'reasoning_effort'}}
    assert len(a['tasks']) == len(set(a['tasks'])) == 10
    assert a['model'] == 'gpt-6.1-sol' and not a['harness']
    assert a['retry_limit'] == a['reinstruction_limit'] == a['seed'] == 0
    assert a['timeout_seconds'] == 600
    assert a['codex_version'] == 'codex-cli 0.162.0-alpha.17.2'
    metas = [json.loads(p.read_text()) for p in (REPOSITORY / 'eval/tasks').glob('*/meta.json')]
    selected = [next(m for m in metas if m['id'] == task) for task in a['tasks']]
    assert all(m['frozen'] is True and m['version'] == 1 and not m['two_session'] for m in selected)
    assert len({m.get('family', m['id']) for m in selected}) == 10
    quotas = [('bug_fix', 3), ('feature_plus_test', 3), ('multiple_requirements', 2), ('constrained_refactoring', 2)]
    assert Counter(m['type'] for m in selected) == dict(quotas)
    expected: list[str] = []
    used: set[str] = set()
    for kind, count in quotas:
        candidates = sorted((m for m in metas if m['type'] == kind and not m['two_session']
                             and m.get('family', m['id']) not in used),
                            key=lambda m: (m.get('family', m['id']), m['id']))
        for m in candidates[:count]:
            expected.append(m['id'])
            used.add(m.get('family', m['id']))
    assert a['tasks'] == expected


def test_snapshot_provenance_and_schema_remain_compatible() -> None:
    prices = json.loads((REPOSITORY / 'eval/prices.yaml').read_text())
    schema = json.loads((REPOSITORY / 'schemas/evaluation-report.schema.json').read_text())
    Draft202012Validator(schema['properties']['metadata']['properties']['pricing'],
                        format_checker=FormatChecker()).validate(prices)
    assert prices['snapshot_id'] == 'openai-standard-short-2026-10-22-v1'
    assert prices['checked_on'] == '2026-10-22'
    assert 'https://developers.openai.com/api/docs/pricing' in prices['source']
    assert 'Standard tier' in prices['source'] and '272K' in prices['source']
    assert 'no price-list version or date' in prices['source']
    assert [(r['model'], r['input_per_million_usd'], r['cached_input_per_million_usd'],
             r['output_per_million_usd']) for r in prices['rates']] == [
                 ('gpt-6.1-sol', 2, .1, 10), ('gpt-6-luna', .1, .01, .5)]


@pytest.mark.parametrize('model,expected', [('gpt-6.1-sol', .0178896), ('gpt-6-luna', .0001 * 3592 / 1000 + .00001 * 54656 / 1000 + .0005 * 524 / 1000)])
def test_pinned_prices_feed_accounting_and_metrics(tmp_path: Path, model: str, expected: float) -> None:
    prices = json.loads((REPOSITORY / 'eval/prices.yaml').read_text())
    events = tmp_path / 'events.jsonl'
    events.write_text(json.dumps({'type': 'turn.completed', 'usage': {
        'input_tokens': 58248, 'cached_input_tokens': 54656, 'output_tokens': 524,
        'reasoning_output_tokens': 400}}) + '\n')
    result = usage(events, 1, model, prices)
    assert result['usd'] == pytest.approx(expected)
    assert result['pricing_ref'] == prices['snapshot_id']
    def cost_metric(cost: float | None) -> dict[str, object]:
        return compute([{'outcome': 'pass', 'attempts': 1, 'two_session': False,
                         'done_claims': {'claimed_items': 0, 'claimed_without_evidence': 0},
                         'costs': {'total_usd': total([cost, 0])}, 'handoff': None}],
                       seed=0, resamples=1000)['cost_per_pass']
    assert cost_metric(result['usd'])['value'] == pytest.approx(expected)
    for unknown in (usage(events, 1, 'unknown', prices), usage(events, 1, model, prices, tier='priority')):
        assert unknown['usd'] is unknown['pricing_ref'] is None
        assert cost_metric(unknown['usd'])['value'] is None
    events.write_text(json.dumps({'type': 'turn.completed', 'service_tier': 'flex', 'usage': {
        'input_tokens': 58248, 'cached_input_tokens': 54656, 'output_tokens': 524}}) + '\n')
    assert usage(events, 1, model, prices)['usd'] is None
    events.write_text(json.dumps({'type': 'turn.completed', 'usage': {
        'input_tokens': 272001, 'cached_input_tokens': 0, 'output_tokens': 524}}) + '\n')
    assert usage(events, 1, model, prices)['usd'] is None


def test_full_configurations_cover_exact_frozen_inventory() -> None:
    from eval.runner.core import load_config
    inventory = sorted(p.parent.name for p in (REPOSITORY / 'eval/tasks').glob('*/meta.json'))
    assert len(inventory) == 120
    configs = [load_config(REPOSITORY / f'eval/configs/full-{letter}.yaml') for letter in 'ab']
    for letter, effort, config in zip('ab', ['medium', 'max'], configs):
        pilot = json.loads((REPOSITORY / f'eval/configs/pilot-{letter}.yaml').read_text())
        assert config['codex_version'] == 'codex-cli 0.163.0-alpha.11.1'
        assert config['tasks'] == inventory
        assert config['reasoning_effort'] == effort and config['harness'] is False
        for key in ('seed', 'retry_limit', 'reinstruction_limit', 'model',
                    'grading_timeout_seconds', 'timeout_seconds', 'control_backend'):
            assert config[key] == pilot[key]
        assert set(config['task_timeout_seconds']) == set(inventory)
        assert sum(2 if json.loads((REPOSITORY / 'eval/tasks' / task / 'meta.json').read_text())['two_session'] else 1
                   for task in config['tasks']) == 140
    assert configs[0]['tasks'] == configs[1]['tasks']
    smoke = load_config(REPOSITORY / 'eval/configs/smoke-two-session-a.yaml')
    assert smoke['tasks'] == ['two-session-prefix-sums']
    assert smoke['model'] == 'gpt-6.1-sol' and smoke['reasoning_effort'] == 'medium'
    assert smoke['harness'] is False
    assert smoke['codex_version'] == 'codex-cli 0.163.0-alpha.11.1'


def test_handoff_success_arithmetic_and_zero_denominators() -> None:
    from eval.metrics import compute
    def task(outcome: str, *, two: bool = True, restated: bool = False) -> dict[str, object]:
        return {'outcome': outcome, 'two_session': two, 'attempts': 2 if two else 1,
                'done_claims': {'claimed_items': 0, 'claimed_without_evidence': 0},
                'costs': {'total_usd': 1},
                'handoff': {'day2_pass': outcome == 'pass', 'user_restated_day1_context': restated} if two else None}
    tasks = [task('pass'), task('fail'), task('pass', restated=True), task('invalid'), task('pass', two=False)]
    metrics = compute(tasks, seed=0, resamples=1000)
    assert metrics['handoff_success']['value'] == pytest.approx(1 / 3)
    assert metrics['handoff_success']['sample_size'] == 3
    assert metrics['avg_attempts']['value'] == 1.75
    for sample in ([], [task('invalid')], [task('pass', two=False)]):
        m = compute(sample, seed=0, resamples=1000)['handoff_success']
        assert m['value'] is m['ci95']['lower'] is m['ci95']['upper'] is None
        assert m['sample_size'] == 0 and m['undefined_reason']
