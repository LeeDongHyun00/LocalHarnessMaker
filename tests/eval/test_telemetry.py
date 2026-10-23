"""Subscription telemetry is evidence, not inferred per-task billing."""

import json
from pathlib import Path
from typing import Any

import pytest

from eval.runner.telemetry import collect, capture_tier
from eval.runner.pricing import select
from eval.runner import core


def test_records_account_snapshots_without_inferring_a_task_charge(tmp_path: Path) -> None:
    events, native = tmp_path / "exec.jsonl", tmp_path / "native.jsonl"
    events.write_text(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 40, "cached_input_tokens": 32, "output_tokens": 7}}) + "\n")
    native.write_text("".join(json.dumps(event) + "\n" for event in [
        {"type": "turn_context", "payload": {"model": "gpt-6.1-sol", "effort": "medium"}},
        {"type": "event_msg", "payload": {"type": "token_count", "rate_limits": {"plan_type": "example", "primary": {"used_percent": 2.0}}}},
    ]))
    data = collect([events], [native], "gpt-6.1-sol", "medium")
    assert data["settings_evidence"]["verified"]
    assert not data["settings_evidence"]["exec_json_exposes_effort"]
    assert data["usage"]["tokens"]["cached_input_tokens"] == 32
    assert data["usage"]["plan_usage"]["availability"] == "account_snapshots"
    assert data["usage"]["plan_usage"]["exact_task_consumption"] is None
    assert data["usage"]["billed_usd"] is None


def test_config_request_alone_does_not_verify_runtime_effort(tmp_path: Path) -> None:
    events = tmp_path / "exec.jsonl"
    events.write_text('{"type":"turn.completed"}\n')
    assert not collect([events], [], "gpt-6.1-sol", "medium")["settings_evidence"]["verified"]


def test_mismatched_runtime_effort_is_unverified(tmp_path: Path) -> None:
    events, native = tmp_path / "exec.jsonl", tmp_path / "native.jsonl"
    events.write_text('{"type":"turn.completed"}\n')
    native.write_text('{"type":"turn_context","payload":{"model":"gpt-6.1-sol","effort":"low"}}\n')
    assert not collect([events], [native], "gpt-6.1-sol", "medium")["settings_evidence"]["verified"]


@pytest.mark.parametrize("source", ["both", "applied_only", "context_only"])
def test_applied_thread_settings_are_runtime_evidence(tmp_path: Path, source: str) -> None:
    fixture = Path(__file__).parent / "fixtures/native-session-0.163.jsonl"
    events = [json.loads(line) for line in fixture.read_text().splitlines()]
    if source == "applied_only":
        events = [e for e in events if e["type"] != "turn_context"]
    elif source == "context_only":
        events = [e for e in events if e.get("payload", {}).get("type") != "thread_settings_applied"]
    native = tmp_path / "native.jsonl"
    native.write_text("".join(json.dumps(e) + "\n" for e in events))
    evidence = collect([], [native], "gpt-6.1-sol", "medium")["settings_evidence"]
    assert evidence["verified"]
    assert len(evidence["observed"]) == (2 if source == "both" else 1)
    assert ("thread_settings_applied" in evidence["source"]) == (source != "context_only")


@pytest.mark.parametrize("source", ["turn_context", "thread_settings_applied"])
@pytest.mark.parametrize("field,value", [("model", "other-model"), ("reasoning_effort", "low")])
def test_conflicting_context_or_applied_settings_are_unverified(tmp_path: Path, source: str,
                                                               field: str, value: str) -> None:
    fixture = Path(__file__).parent / "fixtures/native-session-0.163.jsonl"
    events = [json.loads(line) for line in fixture.read_text().splitlines()]
    event = next(e for e in events if e["type"] == source or e.get("payload", {}).get("type") == source)
    settings = event["payload"] if source == "turn_context" else event["payload"]["thread_settings"]
    settings["effort" if source == "turn_context" and field == "reasoning_effort" else field] = value
    native = tmp_path / "native.jsonl"
    native.write_text("".join(json.dumps(e) + "\n" for e in events))
    assert not collect([], [native], "gpt-6.1-sol", "medium")["settings_evidence"]["verified"]


def test_per_attempt_primary_plan_observations_and_tokens(tmp_path: Path) -> None:
    from eval.runner.telemetry import collect_runs
    events = [tmp_path / f'exec-{i}.jsonl' for i in (1, 2)]
    for i, path in enumerate(events, 1):
        path.write_text(json.dumps({'type': 'turn.completed', 'usage': {'input_tokens': i * 10}}) + '\n')
    native = tmp_path / 'native.jsonl'
    native.write_text(''.join(json.dumps({'type': 'event_msg', 'timestamp': f'2026-10-22T00:00:{second:02d}Z',
        'payload': {'type': 'token_count', 'rate_limits': {'primary': {'used_percent': used}}}}) + '\n'
        for second, used in [(1, 2), (3, 3), (6, 4), (9, 5)]))
    segments = [{'attempt': i, 'started_at': f'2026-10-22T00:00:{start:02d}+00:00',
                 'exited_at': f'2026-10-22T00:00:{end:02d}+00:00'}
                for i, start, end in [(1, 0, 4), (2, 5, 8)]]
    runs = collect_runs(events, [native], segments)
    assert runs[0]['tokens']['input_tokens'] == 10
    assert runs[1]['tokens']['input_tokens'] == 20
    assert runs[0]['plan_usage']['before'] is None
    assert runs[0]['plan_usage']['first_observed_during_run']['primary_used_percent'] == 2
    assert runs[0]['plan_usage']['after']['primary_used_percent'] == 3
    assert runs[1]['plan_usage']['before']['primary_used_percent'] == 3
    assert runs[1]['plan_usage']['after']['primary_used_percent'] == 4
    assert all(run['plan_usage']['exact_task_consumption'] is None for run in runs)
    empty = collect_runs(events[:1], [], segments[:1])[0]['plan_usage']
    assert empty['before'] is empty['after'] is None


def test_native_unknown_tier_is_not_assumed_standard(tmp_path: Path) -> None:
    native = tmp_path / 'native.jsonl'
    native.write_text(json.dumps({'type': 'turn_context', 'payload': {
        'model': 'gpt-6.1-sol', 'effort': 'medium', 'service_tier': 'priority'}}) + '\n')
    assert collect([], [native], 'gpt-6.1-sol', 'medium')['pricing_evidence']['tier'] == 'unknown'


@pytest.mark.parametrize('model,tier', [('gpt-6.1-sol', 'standard'), ('gpt-6-luna', 'priority')])
@pytest.mark.parametrize('record', ['absent', 'omitted', 'null'])
def test_unrequested_tier_uses_model_default_snapshot(tmp_path: Path, model: str, tier: str, record: str) -> None:
    native = tmp_path / 'native.jsonl'
    settings: dict[str, Any] = {'model': model, 'reasoning_effort': 'medium'}
    if record == 'null':
        settings['service_tier'] = None
    applied = {'type': 'event_msg', 'payload': {'type': 'thread_settings_applied', 'thread_settings': settings}}
    native.write_text((json.dumps(applied) + '\n') if record != 'absent' else '')
    prices = json.loads((core.REPOSITORY / 'eval/prices.yaml').read_text())
    for evidence in (collect([], [native], model, 'medium')['pricing_evidence'],
                     capture_tier([native], {}, model=model)):
        assert evidence['tier'] == tier
        assert 'inferred from the model default' in evidence['basis']
        rate, reference = select(prices, model, evidence['tier'])
        assert rate is not None and ('-fast-' in reference) == (tier == 'priority')
    assert capture_tier([native], {}, model=model, service_tier='priority')['tier'] == 'unknown'
    assert not collect([], [native], model, 'medium', 'priority')['settings_evidence']['service_tier_verified']


@pytest.mark.parametrize('value,expected', [('default', 'standard'), ('priority', 'priority'),
                                         ('unknown', 'unknown'), (42, 'unknown')])
def test_explicit_native_tier_is_preserved_without_default_guessing(tmp_path: Path, value: Any, expected: str) -> None:
    native = tmp_path / 'native.jsonl'
    native.write_text(json.dumps({'type': 'event_msg', 'payload': {'type': 'thread_settings_applied',
        'thread_settings': {'service_tier': value}}}) + '\n')
    assert capture_tier([native], {}, model='gpt-6.1-sol')['tier'] == expected
    assert collect([], [native], 'gpt-6.1-sol', 'medium')['pricing_evidence']['tier'] == expected
