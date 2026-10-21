"""Subscription telemetry is evidence, not inferred per-task billing."""

import json
from pathlib import Path

from eval.runner.telemetry import collect


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
