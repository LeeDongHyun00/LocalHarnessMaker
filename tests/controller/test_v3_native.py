"""Authored native rollout and provider-error regressions; no live Codex calls."""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

import pytest

from controller.analyze import Prices
from controller.errors import BackendError
from controller.generation import schema_validator
from controller.settings import PACKAGE_DIR, load_object
from controller.v3 import _audit_validator, run_operation, validate_requirements
from controller.v3_client import MODEL, IdentityUnobserved, PinMismatch, PinnedLunaClient
from controller.v3_wire import REQUIREMENTS
from tests.controller.test_v3 import SESSION, accounting, rows, setup_session

THREAD = "01a171ff-aed8-71f3-adcd-067bc5de1a9f"
FIXTURE = Path(__file__).parent / "fixtures/v3-native/rollout-luna.jsonl"


def install_rollout(home: Path, text: str, thread: str = THREAD) -> Path:
    target = home / "sessions/2026/10/25" / f"rollout-2026-10-25T01-00-00-{thread}.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    return target


def make_client(runner: Any) -> PinnedLunaClient:
    prices = Prices.from_dict(load_object(PACKAGE_DIR / "prices.yaml")["models"][MODEL])
    config = dict(load_object(PACKAGE_DIR / "config.yaml")["codex_cli"], executable="/mock/codex")
    return PinnedLunaClient(prices, "test-pinned", runner=runner, config=config)


def started(thread: str = THREAD) -> str:
    return json.dumps({"type": "thread.started", "thread_id": thread}) + "\n"


def log_calls(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    return [json.loads(record.message.removeprefix("control_call "))
            for record in caplog.records if record.message.startswith("control_call ")]


@pytest.mark.parametrize("completed", [False, True])
@pytest.mark.parametrize("identity", ["applied", "tokens"])
def test_rollout_identity_and_usage_from_child_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture,
    completed: bool, identity: str,
) -> None:
    home = tmp_path / "isolated-codex"
    monkeypatch.setenv("CODEX_HOME", str(home))
    text = FIXTURE.read_text()
    if identity == "tokens":
        events = [json.loads(line) for line in text.splitlines()]
        events = [e for e in events if e.get("payload", {}).get("type") != "thread_settings_applied"]
        for event in events:
            if event.get("payload", {}).get("type") == "token_count":
                event["payload"]["info"]["model"] = MODEL
        text = "\n".join(json.dumps(e) for e in events)

    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert "--ephemeral" not in argv  # V3 needs a persisted native rollout.
        assert kwargs["env"]["CODEX_HOME"] == str(home)
        assert kwargs["env"]["HARNESS_NESTED"] == "1" and kwargs["shell"] is False
        install_rollout(home, text)
        # A concurrent, unrelated rollout must never supply identity or usage.
        install_rollout(home, text.replace(THREAD, "other-thread").replace(MODEL, "other-model"), "other-thread")
        Path(argv[argv.index("-o") + 1]).write_text(json.dumps(rows()))
        events = started()
        if completed:
            events += json.dumps({"type": "turn.completed", "usage": {
                "input_tokens": 100, "cached_input_tokens": 20, "output_tokens": 50}})
        return subprocess.CompletedProcess(argv, 0, events, "")

    client = make_client(runner)
    with caplog.at_level(logging.INFO):
        assert client.generate(REQUIREMENTS, [{"role": "user", "content": "request"}]) == rows()
    assert client.model == MODEL
    usage = client.usage()
    assert (usage.input_tokens, usage.cached_input_tokens, usage.output_tokens) == (
        (100, 20, 50) if completed else (1200, 300, 65))
    expected = (80 * .1 + 20 * .01 + 50 * .5 if completed else 900 * .1 + 300 * .01 + 65 * .5) / 1e6
    assert usage.usd == pytest.approx(expected)  # No cumulative or reasoning double-count.
    call, = log_calls(caplog)
    assert call["status"] == "success" and call["model"] == MODEL
    assert call["input_tokens"] == usage.input_tokens and call["error"] is None


@pytest.mark.parametrize("case", ["missing", "wrong_thread", "wrong_filename", "payload_thread", "assistant", "malformed", "mismatch", "conflict"])
def test_native_identity_failures_never_substitute(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str,
) -> None:
    home = tmp_path / "codex"
    monkeypatch.setenv("CODEX_HOME", str(home))
    text = FIXTURE.read_text()
    if case == "wrong_thread":
        text = text.replace(THREAD, "other-thread")
    elif case == "payload_thread":
        text = text.replace(f'"thread_id":"{THREAD}"', '"thread_id":"other-thread"')
    elif case == "assistant":
        text = json.dumps({"type": "session_meta", "payload": {"id": THREAD}}) + "\n" + json.dumps({
            "type": "response_item", "payload": {"type": "message", "model": MODEL, "text": MODEL}})
    elif case == "malformed":
        text = "not-json"
    elif case == "mismatch":
        text = text.replace(MODEL, "gpt-other")
    elif case == "conflict":
        text += '\n' + json.dumps({"type": "event_msg", "payload": {
            "type": "token_count", "model": "gpt-other"}})
    if case != "missing":
        install_rollout(home, text, "other-thread" if case == "wrong_filename" else THREAD)

    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        Path(argv[argv.index("-o") + 1]).write_text(json.dumps(rows()))
        return subprocess.CompletedProcess(argv, 0, started(), "")

    client = make_client(runner)
    mismatch = case in {"mismatch", "conflict"}
    with pytest.raises(PinMismatch if mismatch else IdentityUnobserved):
        client.generate(REQUIREMENTS, [{"role": "user", "content": "request"}])
    assert client.model == ("gpt-other" if mismatch else None)
    if not mismatch:
        assert client.error == "identity_unobserved"
    with pytest.raises(BackendError, match="second provider invocation"):
        client.generate(REQUIREMENTS, [{"role": "user", "content": "request"}])


def test_default_codex_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CODEX_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    install_rollout(tmp_path / ".codex", FIXTURE.read_text())

    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        Path(argv[argv.index("-o") + 1]).write_text(json.dumps(rows()))
        return subprocess.CompletedProcess(argv, 0, started(), "")

    client = make_client(runner)
    client.generate(REQUIREMENTS, [{"role": "user", "content": "request"}])
    assert client.model == MODEL


@pytest.mark.parametrize("source", ["event", "turn_failed", "stderr"])
@pytest.mark.parametrize("length", [1100, 2400])
def test_complete_provider_error_reaches_control_log_and_public_accounting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture,
    source: str, length: int,
) -> None:
    directory, prompt = setup_session(tmp_path)
    home = tmp_path / "codex"
    monkeypatch.setenv("CODEX_HOME", str(home))
    install_rollout(home, FIXTURE.read_text())
    message = "Invalid schema for response_format: " + "x" * length + " complete provider suffix"
    count = 0

    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal count
        count += 1
        events = started()
        if source == "event":
            events += json.dumps({"type": "error", "message": json.dumps({
                "type": "error", "error": {"message": message}})})
        elif source == "turn_failed":
            events += json.dumps({"type": "turn.failed", "error": {"message": message}})
        return subprocess.CompletedProcess(argv, 1, events, message if source == "stderr" else "unrelated stderr")

    with caplog.at_level(logging.INFO):
        path, code = run_operation("requirements", session_id=SESSION, artifacts=directory,
                                   prompt_path=prompt, client_factory=lambda *_: make_client(runner))
    record, = accounting(directory)
    call, = log_calls(caplog)
    assert code == 2 and load_object(path)["state"] == "unavailable"
    assert record["status"] == call["status"] == "error"
    assert record["model"] == call["model"] == MODEL
    assert record["error"] == call["error"] == message[:2000]
    assert count == 1 and record["input_tokens"] == 1200
    assert (directory / "evidence/requirements-rollout.jsonl").is_file()


@pytest.mark.parametrize("phase", ["requirements", "claim_audit"])
def test_both_native_phases_publish_frozen_schema_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phase: str,
) -> None:
    directory, prompt = setup_session(tmp_path)
    home = tmp_path / "codex"
    monkeypatch.setenv("CODEX_HOME", str(home))
    install_rollout(home, FIXTURE.read_text())
    count = 0

    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        nonlocal count
        count += 1
        value = rows() if count == 1 else {"claims": []}
        wire = load_object(Path(argv[argv.index("--output-schema") + 1]))
        if count == 1:
            assert_provider_subset(wire)
        Path(argv[argv.index("-o") + 1]).write_text(json.dumps(value))
        return subprocess.CompletedProcess(argv, 0, started(), "")

    def factory(*_: Any) -> PinnedLunaClient:
        return make_client(runner)
    requirements, code = run_operation("requirements", session_id=SESSION, artifacts=directory,
                                        prompt_path=prompt, client_factory=factory)
    assert code == 0
    validate_requirements(load_object(requirements), directory, SESSION)
    if phase == "claim_audit":
        final = tmp_path / "final.txt"
        final.write_text("Created answer.py.")
        audit, code = run_operation("claim_audit", session_id=SESSION, artifacts=directory,
                                    requirements_path=requirements, final_path=final, client_factory=factory)
        assert code == 0
        _audit_validator().validate(load_object(audit))
    calls = accounting(directory)
    assert len(calls) == count == (1 if phase == "requirements" else 2)
    assert all(call["model"] == MODEL and call["status"] == "success" for call in calls)


def assert_provider_subset(value: Any) -> None:
    if isinstance(value, list):
        for item in value:
            assert_provider_subset(item)
    elif isinstance(value, dict):
        assert not set(value) & {"format", "minLength", "pattern", "oneOf", "minimum", "minItems", "uniqueItems"}
        if value.get("type") == "object":
            assert value["additionalProperties"] is False
            assert set(value["required"]) == set(value["properties"])
        if "enum" in value:
            assert len({type(item) for item in value["enum"]}) == 1
        for item in value.values():
            assert_provider_subset(item)


@pytest.mark.parametrize("mode", ["empty_rows", "empty_text", "empty_excerpt", "empty_question", "zero", "negative", "duplicate", "missing"])
def test_wire_relaxation_does_not_relax_artifact_semantics(tmp_path: Path, mode: str) -> None:
    from tests.controller.test_v3 import FakeClient, invoke

    directory, prompt = setup_session(tmp_path)
    value = rows()
    if mode == "empty_rows":
        value["requirements"] = []
    elif mode in {"empty_text", "empty_excerpt"}:
        value["requirements"][0]["text" if mode == "empty_text" else "source_excerpt"] = ""
    else:
        numbers = {"zero": [0], "negative": [-1], "duplicate": [1, 1], "missing": [4]}.get(mode, [])
        value["open_questions"] = [{"text": "" if mode == "empty_question" else "Which?", "requirement_numbers": numbers}]
    path, code = invoke(directory, prompt, FakeClient(value))
    assert code == 2 and load_object(path)["state"] == "unavailable"
    schema_validator("requirements.schema.json").validate(load_object(path))
    assert accounting(directory)[0]["status"] == "error"


def test_unobserved_identity_keeps_provider_error_and_disables_pin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture,
) -> None:
    directory, prompt = setup_session(tmp_path)
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "empty-codex"))
    message = "Invalid schema for response_format: " + "detail " * 100 + "provider suffix"

    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 1, started() + json.dumps({
            "type": "error", "message": message}), "")

    with caplog.at_level(logging.INFO):
        path, code = run_operation("requirements", session_id=SESSION, artifacts=directory,
                                   prompt_path=prompt, client_factory=lambda *_: make_client(runner))
    record, = accounting(directory)
    call, = log_calls(caplog)
    assert code == 2 and load_object(path)["state"] == "unavailable"
    assert record["status"] == call["status"] == "error"
    assert record["model"] is call["model"] is None
    assert record["error"] == call["error"] == "identity_unobserved\n" + message
    pin = load_object(directory / "pin-check.json")
    schema_validator("pin-check.schema.json").validate(pin)
    assert pin["status"] == "disabled" and pin["reason_codes"] == ["model_list_unavailable"]


@pytest.mark.parametrize("counts", [None, {}, {"input_tokens": -1, "cached_input_tokens": 0, "output_tokens": 1},
                                    {"input_tokens": 100, "cached_input_tokens": 101, "output_tokens": 1}])
def test_invalid_native_usage_stays_unknown_with_observed_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, counts: Any,
) -> None:
    home = tmp_path / "codex"
    monkeypatch.setenv("CODEX_HOME", str(home))
    events = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
    events[-1]["payload"]["info"]["total_token_usage"] = counts
    install_rollout(home, "\n".join(json.dumps(event) for event in events))

    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        Path(argv[argv.index("-o") + 1]).write_text(json.dumps(rows()))
        return subprocess.CompletedProcess(argv, 0, started(), "")

    client = make_client(runner)
    client.generate(REQUIREMENTS, [{"role": "user", "content": "request"}])
    usage = client.usage()
    assert client.model == MODEL
    assert usage.input_tokens is usage.output_tokens is usage.usd is None
