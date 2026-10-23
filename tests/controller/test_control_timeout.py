"""Offline capacity/deadline regressions without evaluation prompts or live calls."""

import copy
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.error import URLError

import pytest

from controller.__main__ import main
from controller.backends.cheap_api import CheapAPIBackend
from controller.backends.codex_cli import CodexCLIBackend
from controller.backends.local import LocalBackend
from controller.backends.routing import RoutedBackend
from controller.errors import BackendError, InputError
from controller.settings import load_object
from tests.controller.support import ROOT, RecordingTransport
from tests.controller.test_cli import arguments
from tests.controller.test_codex_cli import MockRunner, contract_schema, events


@pytest.mark.parametrize("selected", ["codex_cli", "cheap_api"])
@pytest.mark.parametrize("override", [None, "90", "0.125", " 1.2e2 "])
def test_deadline_snapshot_reaches_transport_and_log(
    selected: str, override: str | None, monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.delenv("HARNESS_CONTROL_TIMEOUT_SECONDS", raising=False)
    if override is not None:
        monkeypatch.setenv("HARNESS_CONTROL_TIMEOUT_SECONDS", override)
    monkeypatch.setenv("OPENAI_API_KEY", "offline-placeholder")
    config = load_object(ROOT / "controller/config.yaml")[selected]
    config["timeout_seconds"] = 17.5
    original = copy.deepcopy(config)
    runner, transport = MockRunner(), RecordingTransport()
    backend = (
        CodexCLIBackend(config=config, runner=runner, executable="/mock/codex")
        if selected == "codex_cli" else CheapAPIBackend(config=config, transport=transport)
    )
    expected = 17.5 if override is None else float(override)
    monkeypatch.setenv("HARNESS_CONTROL_TIMEOUT_SECONDS", "999")
    with caplog.at_level(logging.INFO):
        backend.generate(contract_schema(), [{"role": "user", "content": "Offline request"}])
    actual = runner.calls[0]["kwargs"]["timeout"] if selected == "codex_cli" else transport.calls[0]["timeout"]
    assert actual == expected
    assert config == original
    records = [json.loads(record.getMessage().removeprefix("control_call "))
               for record in caplog.records if record.getMessage().startswith("control_call ")]
    assert len(records) == 1
    assert records[0]["timeout_seconds"] == expected
    assert records[0]["status"] == "success"
    assert "control_failure " not in caplog.text


@pytest.mark.parametrize("selected", ["codex_cli", "cheap_api"])
@pytest.mark.parametrize("value", ["", "bad", "0", "-1", "nan", "inf", "-inf", "1e999"])
def test_invalid_override_rejected_before_calls(
    selected: str, value: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HARNESS_CONTROL_TIMEOUT_SECONDS", value)
    runner, transport = MockRunner(), RecordingTransport()
    with pytest.raises(InputError, match="HARNESS_CONTROL_TIMEOUT_SECONDS"):
        if selected == "codex_cli":
            CodexCLIBackend(runner=runner, executable="/mock/codex")
        else:
            CheapAPIBackend(transport=transport)
    assert not runner.calls and not transport.calls


def test_override_does_not_apply_to_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HARNESS_CONTROL_TIMEOUT_SECONDS", "bad")
    config = load_object(ROOT / "controller/config.yaml")["local"]
    config["enabled"] = True  # Constructor only; no local inference.
    assert LocalBackend(config=config).timeout == 30


def test_non_timeout_is_not_classified_as_deadline(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "offline-placeholder")

    def fail(*args: Any) -> Any:
        raise BackendError("Model error")

    with caplog.at_level(logging.INFO), pytest.raises(BackendError, match="Model error"):
        CheapAPIBackend(transport=fail).generate({}, [])
    assert "control_call " in caplog.text
    assert "control_failure " not in caplog.text


def test_timeout_then_successful_http_fallback_keeps_unknown_accounting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("HARNESS_CONTROL_TIMEOUT_SECONDS", "120")
    monkeypatch.setenv("OPENAI_API_KEY", "offline-placeholder")

    def timeout(argv: list[str], **kwargs: Any) -> Any:
        assert kwargs["timeout"] == 120
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    transport = RecordingTransport()
    routed = RoutedBackend("codex_cli", factories={
        "codex_cli": lambda: CodexCLIBackend(runner=timeout, executable="/mock/codex"),
        "cheap_api": lambda: CheapAPIBackend(transport=transport),
    })
    output = tmp_path / "contract.json"
    with caplog.at_level(logging.INFO):
        assert main(arguments(output), backend_factory=lambda _: routed) == 2
    assert capsys.readouterr().out == "" and not output.exists()
    assert routed.count == 2 and routed.selected == "cheap_api"
    assert routed.usage().input_tokens is None and routed.usage().usd is None
    assert transport.calls[0]["timeout"] == 120
    assert sum(record.getMessage().startswith("control_failure ") for record in caplog.records) == 1
    calls = [json.loads(record.getMessage().removeprefix("control_call "))
             for record in caplog.records if record.getMessage().startswith("control_call ")]
    assert [(call["backend"], call["status"], call["timeout_seconds"]) for call in calls] == [
        ("codex_cli", "error", 120), ("cheap_api", "success", 120),
    ]


@pytest.mark.parametrize("kind", ["cli", "cli-known-usage", "api", "api-url", "api-injected"])
def test_timeout_diagnostic_reaches_stderr_with_honest_exit_two(
    kind: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("HARNESS_CONTROL_TIMEOUT_SECONDS", "87.25")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    selected = "codex_cli" if kind.startswith("cli") else "cheap_api"
    logger = logging.getLogger(f"controller.backends.{selected}")
    monkeypatch.setattr(logger, "handlers", [logging.StreamHandler(sys.stderr)])
    monkeypatch.setattr(logger, "propagate", False)
    monkeypatch.setattr(logger, "level", logging.INFO)
    calls: list[float] = []

    def timeout_runner(argv: list[str], **kwargs: Any) -> Any:
        calls.append(kwargs["timeout"])
        raise subprocess.TimeoutExpired(
            argv, kwargs["timeout"],
            output=events().encode() if kind == "cli-known-usage" else None,
        )

    def timeout_http(*args: Any, **kwargs: Any) -> Any:
        calls.append(kwargs["timeout"])
        error = TimeoutError("private transport details")
        raise URLError(error) if kind == "api-url" else error

    def timeout_transport(*args: Any) -> Any:
        calls.append(args[-1])
        raise TimeoutError("private transport details")

    monkeypatch.setattr("controller.backends.cheap_api.urlopen", timeout_http)
    config = load_object(ROOT / "controller/config.yaml")
    if selected == "cheap_api":
        monkeypatch.setenv("OPENAI_API_KEY", "offline-placeholder")
    backend = (
        CodexCLIBackend(runner=timeout_runner, executable="/mock/codex")
        if selected == "codex_cli" else
        CheapAPIBackend(transport=timeout_transport) if kind == "api-injected" else CheapAPIBackend()
    )
    routed = RoutedBackend(selected, config=config, factories={selected: lambda: backend})
    output = tmp_path / "contract.json"
    output.write_text("existing artifact", encoding="utf-8")
    args = arguments(output)
    args[args.index("--backend") + 1] = selected
    assert main(args, backend_factory=lambda _: routed) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert output.read_text(encoding="utf-8") == "existing artifact"
    assert calls == [87.25]
    failures = [json.loads(line.removeprefix("control_failure "))
                for line in captured.err.splitlines() if line.startswith("control_failure ")]
    assert failures == [{"backend": selected, "model": "gpt-6-luna",
                         "reason": "deadline", "timeout_seconds": 87.25}]
    call = next(json.loads(line.removeprefix("control_call "))
                for line in captured.err.splitlines() if line.startswith("control_call "))
    assert call["timeout_seconds"] == 87.25 and call["status"] == "error"
    if kind == "cli-known-usage":
        assert call["input_tokens"] == 1200 and call["usd"] is not None
    else:
        assert call["input_tokens"] is None and call["output_tokens"] is None and call["usd"] is None
    if selected == "codex_cli":
        assert "CLI fallback requires the same model and an environment API key" in captured.err
    assert "private transport details" not in captured.err
