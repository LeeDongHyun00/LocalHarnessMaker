"""Offline trace and process-boundary diagnostics regressions."""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from controller.__main__ import main
from controller.diagnostics import private_paths, trace
from controller.settings import PACKAGE_DIR, load_object
from controller.v3 import atomic_json
from controller.v3_client import PinnedLunaClient
from tests.controller.test_v3 import SESSION, rows, setup_session


def records(path: Path) -> list[dict[str, Any]]:
    result = [json.loads(line) for line in path.read_text().splitlines()]
    for record in result:
        assert datetime.fromisoformat(record["timestamp"]).tzinfo is not None
    return result


@pytest.mark.parametrize("disabled", [False, True])
def test_cli_trace_success_and_pin_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, disabled: bool,
    capsys: pytest.CaptureFixture[str],
) -> None:
    directory, prompt = setup_session(tmp_path)
    target = tmp_path / "trace.jsonl"
    monkeypatch.setenv("HARNESS_CONTROLLER_TRACE", str(target))
    config = dict(load_object(PACKAGE_DIR / "config.yaml")["codex_cli"],
                  executable=str(Path.home() / "private-bin/codex"))
    stdout = json.dumps({"type": "turn_context", "payload": {"model": "gpt-6-luna"}}) + "\n"
    stderr = "private provider output 한글"
    calls = []

    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        assert kwargs["env"]["HARNESS_NESTED"] == "1"
        Path(argv[argv.index("-o") + 1]).write_text(json.dumps(rows()))
        return subprocess.CompletedProcess(argv, 0, stdout, stderr)

    monkeypatch.setattr("controller.v3.PinnedLunaClient", lambda prices, ref: PinnedLunaClient(
        prices, ref, runner=runner, config=config))
    if disabled:
        pin = load_object(directory / "pin-check.json")
        pin.update(status="disabled", reason_codes=["model_missing"])
        atomic_json(directory / "pin-check.json", pin)
    args = ["requirements", "--prompt", str(prompt), "--session-id", SESSION,
            "--artifacts", str(directory)]
    assert main(args) == (2 if disabled else 0)
    output = capsys.readouterr()
    data = records(target)
    steps = [r["step"] for r in data]
    assert steps[:3] == ["argument_parsing_done", "artifact_directory_validated", "pin_loaded"]
    assert data[-1]["step"] == "final_exit"
    assert data[-1]["exit_code"] == (2 if disabled else 0)
    if disabled:
        assert steps == ["argument_parsing_done", "artifact_directory_validated", "pin_loaded",
                         "exception", "final_exit"]
        assert data[-2]["exception_type"] == "BackendError"
        assert data[-2]["message"] == "pin disabled: reason_codes=['model_missing']"
        assert not calls and not (directory / "luna-calls.jsonl").exists()
        assert "controller:" in output.err
        # Cached unavailable artifacts must also emit a direct diagnostic.
        assert main(args) == 2
        assert "controller:" in capsys.readouterr().err
    else:
        assert steps == ["argument_parsing_done", "artifact_directory_validated", "pin_loaded",
                         "pricing_compared", "executable_resolved", "child_start", "child_exit", "final_exit"]
        assert data[4]["path"] == config["executable"]
        assert data[5]["argv"] == [calls[0][0], *map(private_paths, calls[0][1:])]
        assert data[5]["environment_keys_set"] == ["HARNESS_NESTED"]
        assert data[6]["stdout_bytes"] == len(stdout.encode())
        assert data[6]["stderr_bytes"] == len(stderr.encode())
        assert data[6]["exit_code"] == 0 and data[6]["elapsed_seconds"] >= 0
    serialized = target.read_text()
    assert prompt.read_text() not in serialized and stderr not in serialized and stdout not in serialized
    trace("appended")
    assert records(target)[-1]["step"] == "appended"


@pytest.mark.parametrize("failure", ["RuntimeError('private provider body')", "KeyboardInterrupt()", "SystemExit(0)"])
def test_uncaught_failure_exits_two_with_flushed_pipe_stderr(
    tmp_path: Path, failure: str,
) -> None:
    target = tmp_path / "trace.jsonl"
    # Exercise the real module entry point with stderr captured as a pipe.
    script = f'''
import runpy
import controller.v3

def fail(*args, **kwargs):
    raise {failure}
controller.v3.run_operation = fail
runpy.run_module("controller", run_name="__main__")
'''
    result = subprocess.run([sys.executable, "-c", script, "requirements", "--prompt", "unused",
                             "--session-id", "unused", "--artifacts", "unused"],
                            env={**os.environ, "HARNESS_CONTROLLER_TRACE": str(target)},
                            capture_output=True, text=True, check=False, timeout=10)
    assert result.returncode == 2 and result.stdout == ""
    assert "controller:" in result.stderr and failure.split("(")[0] in result.stderr
    assert "private provider body" not in result.stderr + target.read_text()
    assert records(target)[-1]["exit_code"] == 2


def test_boundary_setup_failure_and_handler_flush(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import controller.__main__ as cli
    flushed = []

    class Handler(logging.Handler):
        def flush(self) -> None:
            flushed.append(True)

    handler = Handler()
    logging.getLogger("controller").addHandler(handler)
    try:
        def fail(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("private provider body")
        monkeypatch.setattr(cli, "_main", fail)
        assert cli.main([]) == 2
        assert "RuntimeError" in capsys.readouterr().err and flushed
    finally:
        logging.getLogger("controller").removeHandler(handler)


def test_help_is_success_and_unwritable_trace_is_optional(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HARNESS_CONTROLLER_TRACE", str(tmp_path / "missing/trace.jsonl"))
    assert main(["--help"]) == 0
    assert main(["requirements"]) == 1


@pytest.mark.parametrize("mode", ["timeout", "spawn", "nonzero"])
def test_child_failure_trace_counts_without_provider_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str,
) -> None:
    from controller.backends.codex_cli import CodexCLIBackend
    from controller.errors import BackendError

    target = tmp_path / "trace.jsonl"
    monkeypatch.setenv("HARNESS_CONTROLLER_TRACE", str(target))
    raw = "private payload 한글".encode()

    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if mode == "timeout":
            raise subprocess.TimeoutExpired(argv, 1, output=raw, stderr=raw)
        if mode == "spawn":
            raise OSError("private payload")
        return subprocess.CompletedProcess(argv, 7, raw.decode(), raw.decode())

    backend = CodexCLIBackend(runner=runner, executable="/mock/codex")
    with pytest.raises(BackendError):
        backend.generate({"type": "object"}, [{"role": "user", "content": "private prompt"}])
    data = records(target)
    child = next(r for r in data if r["step"] == "child_exit")
    assert child["exit_code"] == (7 if mode == "nonzero" else None)
    assert child["stdout_bytes"] == child["stderr_bytes"] == (0 if mode == "spawn" else len(raw))
    assert child["elapsed_seconds"] >= 0
    assert "private payload" not in target.read_text() and "private prompt" not in target.read_text()


def test_home_paths_redacted_except_explicit_executable() -> None:
    assert private_paths(str(Path.home() / "secret/file")) == "<home-path>"
    assert private_paths("/Users/someone/private/file") == "<home-path>"
