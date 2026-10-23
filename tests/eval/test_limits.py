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


CAPACITY = 'Selected model is at capacity. Please try a different model.'
CAPACITY_EVENTS = [
    {'type': 'error', 'message': CAPACITY},
    {'type': 'turn.failed', 'error': {'message': CAPACITY}},
]


@pytest.mark.parametrize('index', [0, 1])
@pytest.mark.parametrize('envelope', [False, True])
def test_capacity_exact_events(tmp_path: Path, index: int, envelope: bool) -> None:
    from eval.runner.limits import capacity_message
    text = json.dumps(CAPACITY_EVENTS[index]) + '\n'
    if envelope:
        text = 'INFO:verifier:control_cli_events ' + json.dumps({'model': 'gpt-6-luna', 'events': text})
    path = tmp_path / 'events'
    path.write_text(text)
    assert capacity_message([path]) == CAPACITY
    path.write_text(json.dumps({'type': 'error', 'message': CAPACITY.upper()}))
    assert capacity_message([path]) == CAPACITY.upper()


@pytest.mark.parametrize('text', ['Server busy', 'Rate limit reached', 'Capacity unavailable'])
def test_other_service_wording_is_not_capacity(tmp_path: Path, text: str) -> None:
    from eval.runner.limits import capacity_message
    path = tmp_path / 'events'
    path.write_text(json.dumps({'type': 'error', 'message': text}))
    assert capacity_message([path]) is None


def test_capacity_prose_and_items_are_not_errors(tmp_path: Path) -> None:
    from eval.runner.limits import capacity_message, capacity_refusal_without_items
    path = tmp_path / 'events'
    item = {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': CAPACITY}}
    path.write_text(json.dumps(item))
    assert capacity_message([path]) is None
    assert capacity_refusal_without_items(CAPACITY_EVENTS)
    assert not capacity_refusal_without_items([item, *CAPACITY_EVENTS])
    assert not capacity_refusal_without_items([{'type': 'item.started'}, *CAPACITY_EVENTS])
