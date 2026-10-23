"""The stderr protocol is tested with injected children, never controller calls."""

from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import signal
import subprocess
from typing import Any

import pytest

from verifier.__main__ import main
from verifier.judge import judge_criterion
from verifier.processes import ProcessGroups, shutdown_scope


CALL1 = 'control_call {"call_id":"one"}\n'
CALL2 = 'control_call {"call_id":"two"}\n'
EVENT = 'control_cli_events {"path":"events.jsonl"}\n'


class Child:
    def __init__(self, mode: str, stderr: str) -> None:
        self.mode, self.log = mode, stderr
        self.now = 0.0
        self.pid = 12345
        self.returncode: int | None = None
        self.stdin, self.stdout, self.stderr = io.BytesIO(), io.BytesIO(), io.BytesIO()
        self.communications = 0
        self.output: Path | None = None
        self.owner = ProcessGroups(clock=lambda: self.now, kill_group=self.kill, sleep=self.sleep)

    def sleep(self, seconds: float) -> None:
        self.now += seconds

    def kill(self, pid: int, sig: int) -> None:
        assert pid == self.pid
        if sig and self.returncode is None:
            self.returncode = -sig

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, timeout: float) -> int | None:
        return self.returncode

    def launch(self, argv: list[str], **kwargs: Any) -> Child:
        if self.mode == "not_launched":
            raise OSError("no executable")
        self.output = Path(argv[argv.index("--out") + 1])
        criterion = json.loads(Path(argv[argv.index("--criterion") + 1]).read_text())
        self.output.write_text(json.dumps({
            "criterion_id": criterion["id"], "status": "pass", "reason": "exact judge reason",
            "evidence": "llm_judge: exact evidence", "model": "mock",
            "usage": {"input_tokens": None, "cached_input_tokens": None, "output_tokens": None,
                      "usd": None, "latency_seconds": 0, "cost_basis": "api_equivalent_usd",
                      "pricing_ref": None},
        }))
        return self

    def communicate(self, input: str | None, timeout: float) -> tuple[str, str]:
        self.communications += 1
        if self.mode in {"timeout", "truncated", "unreadable", "shutdown"}:
            self.now += timeout
            if self.mode == "truncated":
                self.returncode = 0
            if self.mode == "unreadable" and self.communications > 1:
                raise OSError("pipe read failed")
            if self.mode == "shutdown" and self.communications > 1:
                from verifier.processes import Shutdown
                raise Shutdown(signal.SIGTERM)
            raise subprocess.TimeoutExpired("mock", timeout,
                                            output=(str(self.output) + "\n").encode(),
                                            stderr=self.log.encode())
        self.returncode = 7 if self.mode == "failed" else -9 if self.mode == "killed" else 0
        return str(self.output) + "\n", self.log


def inject(monkeypatch: pytest.MonkeyPatch, child: Child) -> None:
    monkeypatch.setattr(subprocess, "Popen", child.launch)
    monkeypatch.setattr("verifier.processes.time.monotonic", lambda: child.now)
    monkeypatch.setattr("verifier.__main__.shutdown_scope", lambda: shutdown_scope(child.owner))


def summary(outcome: str, complete: bool, calls: int, criterion_id: str = "SC-4") -> str:
    return "judge_delegation " + json.dumps({
        "accounting_complete": complete, "backend": "codex_cli", "criterion_id": criterion_id,
        "forwarded_control_calls": calls, "outcome": outcome,
    }, sort_keys=True, separators=(",", ":")) + "\n"


@pytest.mark.parametrize("mode,outcome,complete", [
    ("completed", "completed", True), ("failed", "failed", True),
    ("timeout", "timeout", False), ("truncated", "completed", False),
    ("unreadable", "failed", False), ("killed", "failed", False),
])
def test_accounting_forwarded_in_order_on_every_child_outcome(
    mode: str, outcome: str, complete: bool, contract: dict[str, Any], workspace: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    child = Child(mode, "private diagnostic\n" + CALL1 + EVENT + " control_call ignored\n" + CALL2)
    inject(monkeypatch, child)
    with shutdown_scope(child.owner):
        result = judge_criterion(contract["success_criteria"][3], workspace, timeout=0.1)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == CALL1 + EVENT + CALL2 + summary(outcome, complete, 2)
    assert result.status == ("pass" if mode in {"completed", "truncated"} else "unverifiable")
    assert child.stdin.closed and child.stdout.closed and child.stderr.closed
    if mode == "completed":
        assert result.evidence == "llm_judge: exact evidence"
        assert result.reason == "exact judge reason"
    if mode == "timeout":
        assert child.returncode == -signal.SIGTERM
        assert result.reason == "judge delegation timed out after 0.1 seconds"


@pytest.mark.parametrize("mode,log,expected", [
    ("completed", "diagnostic\n" + EVENT, EVENT + summary("completed", False, 0)),
    ("not_launched", "", summary("not_launched", True, 0)),
    ("completed", CALL1.rstrip("\n"), CALL1 + summary("completed", True, 1)),
])
def test_empty_accounting_launch_failure_and_unterminated_record(
    mode: str, log: str, expected: str, contract: dict[str, Any], workspace: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    child = Child(mode, log)
    inject(monkeypatch, child)
    with shutdown_scope(child.owner):
        judge_criterion(contract["success_criteria"][3], workspace)
    assert capsys.readouterr().err == expected


def test_accounting_interleaves_with_elapsed_and_unstarted_budget_is_silent(
    contract: dict[str, Any], workspace: Path, transcript: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    first = contract["success_criteria"][3]
    second = copy.deepcopy(first)
    second["id"] = "SC-5"
    contract["success_criteria"] = [
        {"id": "SC-1", "description": "exists", "check": {"type": "file_exists", "path": "report.txt"}},
        first, second,
    ]
    child = Child("timeout", CALL1 + EVENT + CALL2)
    inject(monkeypatch, child)
    monkeypatch.setenv("HARNESS_VERIFY_BUDGET_SECONDS", "2.1")
    # check_contract's default clock was bound at import; inject the same clock.
    from verifier.check import check_contract
    monkeypatch.setattr("verifier.__main__.check_contract",
                        lambda *args, **kwargs: check_contract(*args, **kwargs, clock=lambda: child.now))
    source, output = workspace / "contract.json", workspace / "verdict.json"
    source.write_text(json.dumps(contract))
    assert main(["check", "--contract", str(source), "--workspace", str(workspace),
                 "--transcript", str(transcript), "--attempt", "1", "--out", str(output)]) == 0
    captured = capsys.readouterr()
    assert captured.out == str(output) + "\n"
    lines = captured.err.splitlines(keepends=True)
    assert lines[:4] == [CALL1, EVENT, CALL2, summary("timeout", False, 2)]
    assert len(lines) == 5 and lines[4].startswith("verifier elapsed_seconds=")
    verdict = json.loads(output.read_text())
    assert "budget" in verdict["items"][-1]["reason"]


def test_summary_is_flushed_on_shutdown(
    contract: dict[str, Any], workspace: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from verifier.processes import Shutdown

    class Stderr(io.StringIO):
        flushed = False

        def flush(self) -> None:
            self.flushed = True

    child = Child("shutdown", CALL1 + EVENT)
    inject(monkeypatch, child)
    sink = Stderr()
    monkeypatch.setattr("verifier.judge.sys.stderr", sink)
    with shutdown_scope(child.owner), pytest.raises(Shutdown):
        judge_criterion(contract["success_criteria"][3], workspace)
    assert sink.getvalue() == CALL1 + EVENT + summary("failed", False, 1)
    assert sink.flushed
