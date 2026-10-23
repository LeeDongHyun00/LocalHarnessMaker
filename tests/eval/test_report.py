"""Approved report schema, bootstrap and accounting regression coverage."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, Resource

from eval.metrics import compute, metric
from eval.runner.core import REPOSITORY
from eval.runner.report import usage, validate


def task(outcome: str = 'pass', usd: float | None = 1) -> dict:
    return {'outcome': outcome, 'attempts': 2, 'two_session': False,
            'done_claims': {'claimed_items': 2, 'claimed_without_evidence': 1},
            'costs': {'total_usd': usd}, 'handoff': None}


def test_task_cluster_metrics_are_seeded_and_keep_invalid_costs() -> None:
    tasks = [task(), task('invalid', 3)]
    result = compute(tasks, seed=7, resamples=1000)
    assert result == compute(tasks, seed=7, resamples=1000)
    assert result['pass_rate']['value'] == 1
    assert result['pass_rate']['sample_size'] == 1
    assert result['avg_attempts']['value'] == 2
    assert result['false_done_rate']['value'] == .5
    assert result['false_done_rate']['sample_size'] == 2
    assert result['cost_per_pass']['sample_size'] == 2
    assert result['cost_per_pass']['value'] is None  # all-invalid bootstrap replicate
    assert 'bootstrap' in result['cost_per_pass']['undefined_reason']
    assert result['parity']['value'] is None


def test_unknown_cost_and_zero_denominators_never_become_zero() -> None:
    assert compute([task(usd=None)], seed=0, resamples=1000)['cost_per_pass']['value'] is None
    result = compute([], seed=0, resamples=1000)
    assert all(m['value'] is None for m in result.values())
    with pytest.raises(ValueError, match='1000'):
        metric([], 'valid_task', 0, lambda _: None, seed=0, resamples=999)


def test_interval_uses_linear_percentiles_and_whole_task_claims() -> None:
    result = compute([task(), task('fail')], seed=4, resamples=1000)
    assert result['pass_rate']['ci95']['lower'] == 0
    assert result['pass_rate']['ci95']['upper'] == 1
    assert result['false_done_rate']['value'] == .5


def test_cache_and_reasoning_are_not_double_counted(tmp_path: Path) -> None:
    events = tmp_path / 'events.jsonl'
    events.write_text(json.dumps({'type': 'turn.completed', 'usage': {
        'input_tokens': 1000, 'cached_input_tokens': 120, 'output_tokens': 100, 'reasoning_output_tokens': 60}}) + '\n')
    prices = {'snapshot_id': 'synthetic-v1', 'rates': [{'model': 'synthetic',
              'input_per_million_usd': 1, 'cached_input_per_million_usd': .5, 'output_per_million_usd': 2}]}
    assert usage(events, 1, 'synthetic', prices, tier='standard')['usd'] == pytest.approx(.00114)
    assert usage(events, 1, 'unpriced', prices)['usd'] is None
    events.write_text('{"type":"turn.failed"}\n')
    assert usage(events, 1, 'synthetic', prices, tier='standard')['input_tokens'] is None
    events.write_text('{"type":"turn.completed","usage":{"input_tokens":1,"cached_input_tokens":2,"output_tokens":0}}\n')
    with pytest.raises(ValueError, match='Cached'):
        usage(events, 1, 'synthetic', prices, tier='standard')


def test_retired_schema_is_only_an_offline_reference_to_shared_schema() -> None:
    shared = REPOSITORY / 'schemas/evaluation-report.schema.json'
    resource = Resource.from_contents(json.loads(shared.read_text()))
    registry = Registry().with_resource(shared.as_uri(), resource)
    retired = json.loads((REPOSITORY / 'eval/report.schema.json').read_text())
    assert retired['$ref'] == '../schemas/evaluation-report.schema.json'
    # Validate resolving from the shim's actual location, with no network loader.
    shim_path = REPOSITORY / 'eval/report.schema.json'
    registry = registry.with_resource(shim_path.as_uri(), Resource.from_contents(retired))
    shim = {'$ref': shim_path.as_uri()}
    with pytest.raises(ValidationError):
        Draft202012Validator(shim, registry=registry).validate({'format': 'eval-baseline-provisional-v1'})


def test_bootstrap_seed_controls_non_degenerate_samples() -> None:
    clusters = [{'value': value} for value in [0, 1, 4, 9, 20, 43, 91]]
    statistic = lambda sample: sum(item['value'] for item in sample) / len(sample)
    first = metric(clusters, 'valid_task', len(clusters), statistic, seed=7, resamples=1000)
    assert first == metric(clusters, 'valid_task', len(clusters), statistic, seed=7, resamples=1000)
    assert first['ci95'] != metric(clusters, 'valid_task', len(clusters), statistic, seed=8, resamples=1000)['ci95']
