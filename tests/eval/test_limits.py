"""Account limits are structured infrastructure evidence, not assistant prose."""

import json
from pathlib import Path

import pytest

from eval.runner.limits import usage_limit_message


FIXTURE = Path(__file__).parent / "fixtures/usage-limit.jsonl"
MESSAGE = json.loads(FIXTURE.read_text().splitlines()[0])["message"]


@pytest.mark.parametrize("selection", [slice(None), slice(0, 1), slice(1, 2)])
@pytest.mark.parametrize("envelope", [False, True])
def test_exact_usage_limit_error_and_turn_failed(tmp_path: Path, selection: slice, envelope: bool) -> None:
    stream = "\n".join(FIXTURE.read_text().splitlines()[selection]) + "\n"
    if envelope:
        stream = 'control_cli_events ' + json.dumps({"model": "gpt-6-luna", "events": stream}) + "\n"
    path = tmp_path / "stream"
    path.write_text(stream)
    assert usage_limit_message([path]) == MESSAGE


@pytest.mark.parametrize("event", [
    {"type": "error", "message": "Transport unavailable"},
    {"type": "turn.failed", "error": {"message": "Task timeout"}},
    {"type": "item.completed", "item": {"type": "agent_message", "text": MESSAGE}},
    {"type": "item.completed", "item": {"type": "command_execution", "aggregated_output": MESSAGE}},
    {"type": "turn.failed", "error": None},
    {"type": "turn.failed", "error": {"message": [MESSAGE]}},
    {"type": "unrecognized", "message": MESSAGE},
])
def test_non_limit_errors_and_prose_do_not_halt(tmp_path: Path, event: dict[str, object]) -> None:
    path = tmp_path / "stream"
    path.write_text(json.dumps(event) + "\n" + MESSAGE + "\n")
    assert usage_limit_message([path]) is None


def test_turn_failed_direct_message_and_malformed_logs(tmp_path: Path) -> None:
    path = tmp_path / "stream"
    path.write_text('broken JSON\ncontrol_cli_events {malformed\n' +
                    json.dumps({"type": "turn.failed", "message": MESSAGE}) + "\n")
    assert usage_limit_message([tmp_path / "missing", path]) == MESSAGE
