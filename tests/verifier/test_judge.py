from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from typing import Any

import pytest
from jsonschema import ValidationError

from verifier.check import check_contract
from verifier.judge import judge_criterion, run_judge


@pytest.fixture
def criterion(contract: dict[str, Any]) -> dict[str, Any]:
    return contract["success_criteria"][3]


@pytest.fixture
def judgment() -> dict[str, Any]:
    return {"criterion_id": "SC-4", "status": "pass", "reason": "Exact judge reason.\nSecond line.",
            "evidence": "llm_judge: exact evidence\nwith another line", "model": "gpt-6-luna",
            "usage": {"input_tokens": None, "cached_input_tokens": None, "output_tokens": None,
                      "usd": None, "latency_seconds": 0.01, "cost_basis": "api_equivalent_usd",
                      "pricing_ref": None}}


def mock_judge(monkeypatch: pytest.MonkeyPatch, judgment: Any, *, stdout: str | None = None,
               exit_code: int = 0, write: bool = True) -> list[tuple[list[str], dict[str, Any]]]:
    calls: list[tuple[list[str], dict[str, Any]]] = []

    def run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append((argv, kwargs))
        output = Path(argv[argv.index("--out") + 1])
        if write:
            output.write_text(json.dumps(judgment))
        return subprocess.CompletedProcess(argv, exit_code, str(output) + "\n" if stdout is None else stdout, "mock log")

    monkeypatch.setattr("verifier.judge.run_judge", run)
    return calls


@pytest.mark.parametrize("status", ["pass", "fail", "unverifiable"])
def test_valid_judgment_preserved(criterion: dict[str, Any], judgment: dict[str, Any], workspace: Path,
                                 monkeypatch: pytest.MonkeyPatch, status: str) -> None:
    judgment["status"] = status
    calls = mock_judge(monkeypatch, judgment)
    result = judge_criterion(criterion, workspace)
    assert (result.status, result.reason, result.evidence) == (status, judgment["reason"], judgment["evidence"])
    assert len(calls) == 1


@pytest.mark.parametrize("backend", ["codex_cli", "cheap_api", "local"])
def test_subprocess_boundary(criterion: dict[str, Any], judgment: dict[str, Any], workspace: Path,
                            monkeypatch: pytest.MonkeyPatch, backend: str) -> None:
    parent = dict(os.environ)
    captured: list[dict[str, Any]] = []

    def run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert argv[:4] == [sys.executable, "-m", "controller", "judge"]
        source = Path(argv[argv.index("--criterion") + 1])
        assert json.loads(source.read_text()) == criterion
        assert argv[argv.index("--artifact") + 1] == str(workspace.resolve())
        assert argv[argv.index("--backend") + 1] == backend
        assert kwargs["timeout"] == 9.0
        assert kwargs["env"] == {**parent, "HARNESS_NESTED": "1"}
        assert kwargs["env"] is not os.environ
        output = Path(argv[argv.index("--out") + 1])
        output.write_text(json.dumps(judgment))
        captured.append(kwargs)
        return subprocess.CompletedProcess(argv, 0, str(output) + "\n", "")

    monkeypatch.setattr("verifier.judge.run_judge", run)
    assert judge_criterion(criterion, workspace, backend, timeout=9.0).status == "pass"
    assert len(captured) == 1 and dict(os.environ) == parent


@pytest.mark.parametrize("damage", ["id", "marker", "extra", "missing", "status", "cache", "cost", "type"])
def test_invalid_judgment_rejected(criterion: dict[str, Any], judgment: dict[str, Any], workspace: Path,
                                   monkeypatch: pytest.MonkeyPatch, damage: str) -> None:
    if damage == "id":
        judgment["criterion_id"] = "SC-wrong"
    elif damage == "marker":
        judgment["evidence"] = "marker missing"
    elif damage == "extra":
        judgment["extra"] = True
    elif damage == "missing":
        del judgment["reason"]
    elif damage == "status":
        judgment["status"] = "done"
    elif damage == "cache":
        judgment["usage"].update(input_tokens=1, cached_input_tokens=2)
    elif damage == "cost":
        judgment["usage"]["usd"] = 0.0
    elif damage == "type":
        judgment = []
    mock_judge(monkeypatch, judgment)
    result = judge_criterion(criterion, workspace)
    assert result.status == "unverifiable"
    assert "llm_judge" in result.evidence and "delegation unavailable" in result.reason


@pytest.mark.parametrize("failure", ["exit1", "exit2", "stdout", "missing", "json", "timeout", "oserror"])
def test_transport_failures(criterion: dict[str, Any], judgment: dict[str, Any], workspace: Path,
                            monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    if failure in {"timeout", "oserror", "json"}:
        def broken(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
            if failure == "timeout":
                raise subprocess.TimeoutExpired(argv, kwargs["timeout"])
            if failure == "oserror":
                raise OSError("mock unavailable executable")
            output = Path(argv[argv.index("--out") + 1])
            output.write_text("invalid JSON")
            return subprocess.CompletedProcess(argv, 0, str(output) + "\n", "")
        monkeypatch.setattr("verifier.judge.run_judge", broken)
    else:
        mock_judge(monkeypatch, judgment, exit_code=int(failure[-1]) if failure.startswith("exit") else 0,
                   stdout="extra text\n" if failure == "stdout" else None, write=failure != "missing")
    result = judge_criterion(criterion, workspace)
    assert result.status == "unverifiable" and "llm_judge" in result.evidence
    if failure == "timeout":
        assert result.reason == "judge delegation timed out after 120 seconds"


@pytest.mark.parametrize("damage", ["mechanical", "wrapper", "backend", "artifact", "timeout"])
def test_input_validation_before_subprocess(criterion: dict[str, Any], workspace: Path,
                                           monkeypatch: pytest.MonkeyPatch, damage: str) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("input errors must not launch controller")

    monkeypatch.setattr("verifier.judge.run_judge", forbidden)
    if damage == "mechanical":
        criterion["check"] = {"type": "file_exists", "path": "report.txt"}
    elif damage == "wrapper":
        criterion = {"success_criteria": [criterion]}
    with pytest.raises((ValueError, ValidationError)):
        judge_criterion(criterion, workspace / "absent" if damage == "artifact" else workspace,
                        "invalid" if damage == "backend" else "codex_cli",
                        timeout=0 if damage == "timeout" else 120)


@pytest.mark.parametrize("status", ["pass", "fail", "unverifiable"])
def test_mixed_contract_delegates_only_judge(contract: dict[str, Any], criterion: dict[str, Any],
                                            judgment: dict[str, Any], workspace: Path, transcript: Path,
                                            monkeypatch: pytest.MonkeyPatch, status: str) -> None:
    contract["success_criteria"] = [{"id": "SC-1", "description": "File exists", "check": {
        "type": "file_exists", "path": "report.txt"}}, copy.deepcopy(criterion)]
    monkeypatch.setenv("HARNESS_BACKEND", "local")
    judgment["status"] = status
    calls = mock_judge(monkeypatch, judgment)
    verdict = check_contract(contract, workspace, transcript, 1)
    assert verdict["overall"] == ("pass" if status == "pass" else "fail")
    assert verdict["items"][1] == {"id": "SC-4", "status": status, "reason": judgment["reason"],
                                     "evidence": judgment["evidence"]}
    assert len(calls) == 1
    assert calls[0][0][calls[0][0].index("--backend") + 1] == "local"


def test_all_judge_quality_warning_does_not_delegate(contract: dict[str, Any], criterion: dict[str, Any],
                                                     workspace: Path, transcript: Path,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    contract["success_criteria"] = [criterion]

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("all-judge quality warning must not call controller")

    monkeypatch.setattr("verifier.judge.run_judge", forbidden)
    verdict = check_contract(contract, workspace, transcript, 1)
    assert verdict["overall"] == "fail" and verdict["items"][0]["status"] == "unverifiable"
    assert verdict["reinstruct_message"] is not None


@pytest.mark.parametrize("deadline", [None, "7.5"])
def test_unset_backend_and_configured_deadline(
    contract: dict[str, Any], criterion: dict[str, Any], judgment: dict[str, Any],
    workspace: Path, transcript: Path, monkeypatch: pytest.MonkeyPatch, deadline: str | None,
) -> None:
    for name in ("HARNESS_MAX_ATTEMPTS", "HARNESS_BACKEND", "HARNESS_JUDGE_TIMEOUT_SECONDS"):
        monkeypatch.delenv(name, raising=False)
        assert name not in os.environ
    if deadline is not None:
        monkeypatch.setenv("HARNESS_JUDGE_TIMEOUT_SECONDS", deadline)
    contract["success_criteria"] = [{"id": "SC-1", "description": "File exists", "check": {
        "type": "file_exists", "path": "report.txt"}}, criterion]
    calls = mock_judge(monkeypatch, judgment)
    assert check_contract(contract, workspace, transcript, 1)["overall"] == "pass"
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv[argv.index("--backend") + 1] == "codex_cli"
    assert kwargs["timeout"] == (120.0 if deadline is None else 7.5)


@pytest.mark.parametrize("deadline", ["invalid", "0", "-1", "nan", "inf"])
def test_invalid_deadline_before_execution(
    contract: dict[str, Any], workspace: Path, transcript: Path,
    monkeypatch: pytest.MonkeyPatch, deadline: str,
) -> None:
    monkeypatch.setenv("HARNESS_JUDGE_TIMEOUT_SECONDS", deadline)

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("invalid deadline must not launch a command or judge")

    monkeypatch.setattr("verifier.judge.run_judge", forbidden)
    with pytest.raises(ValueError):
        check_contract(contract, workspace, transcript, 1, forbidden)


@pytest.mark.parametrize("outcome", ["success", "timeout", "error", "already_exited"])
def test_process_group_lifecycle_with_injected_runner_and_clock(
    criterion: dict[str, Any], judgment: dict[str, Any], workspace: Path,
    monkeypatch: pytest.MonkeyPatch, outcome: str,
) -> None:
    events: list[str] = []
    members = {12345, 12346}  # Controller and its Codex grandchild.
    ticks = iter((100.0, 100.25))
    launched: list[dict[str, Any]] = []

    class Process:
        pid = 12345
        returncode: int | None = None

        def communicate(self, input: str | None = None, timeout: float | None = None) -> tuple[str, str]:
            if not events:
                events.append("communicate")
                assert input == "" and timeout == 8.75
                if outcome == "timeout":
                    raise subprocess.TimeoutExpired("mock controller judge", timeout)
                if outcome == "error":
                    raise OSError("mock pipe failure")
                self.returncode = 0
                members.discard(self.pid)
                if outcome == "already_exited":
                    members.clear()
                return str(output) + "\n", ""
            events.append("reap")
            assert not members
            assert timeout is None and input is None
            if self.returncode is None:
                self.returncode = -signal.SIGKILL
            return "", ""

    process = Process()
    output = workspace / "unused"

    def launch(argv: list[str], **kwargs: Any) -> Any:
        nonlocal output
        assert argv[:4] == [sys.executable, "-m", "controller", "judge"]
        assert kwargs["start_new_session"] is True and kwargs["shell"] is False
        assert kwargs["text"] is True
        assert kwargs["stdin"] == kwargs["stdout"] == kwargs["stderr"] == subprocess.PIPE
        assert kwargs["env"]["HARNESS_NESTED"] == "1"
        launched.append(kwargs)
        output = Path(argv[argv.index("--out") + 1])
        output.write_text(json.dumps(judgment))
        return process

    def kill_group(pid: int, sig: int) -> None:
        events.append("kill_group")
        assert pid == process.pid and sig == signal.SIGKILL
        if not members:
            raise ProcessLookupError("group already exited")
        members.clear()

    def run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return run_judge(argv, **kwargs, runner=launch, clock=lambda: next(ticks), kill_group=kill_group)

    monkeypatch.setattr("verifier.judge.run_judge", run)
    result = judge_criterion(criterion, workspace, timeout=9.0)
    assert len(launched) == 1
    assert events == ["communicate", "kill_group", "reap"]
    assert not members
    if outcome in {"success", "already_exited"}:
        assert result.status == "pass"
    else:
        assert result.status == "unverifiable"
        assert "llm_judge" in result.evidence
        assert ("timed out after 9 seconds" if outcome == "timeout" else "unavailable") in result.reason


def test_spawn_failure_does_not_signal_a_group(workspace: Path) -> None:
    def launch(*args: Any, **kwargs: Any) -> Any:
        raise OSError("mock executable unavailable")

    def forbidden(*args: Any) -> None:
        raise AssertionError("no process group was created")

    with pytest.raises(OSError, match="executable unavailable"):
        run_judge(["mock"], cwd=workspace, env={}, timeout=1.0,
                  runner=launch, clock=lambda: 0.0, kill_group=forbidden)
