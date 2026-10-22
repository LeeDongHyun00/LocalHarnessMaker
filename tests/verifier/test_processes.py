"""Injected process trees exercise shutdown without launching workspace code."""

from __future__ import annotations

from contextlib import contextmanager
import errno
import io
import json
from pathlib import Path
import signal
import subprocess
from typing import Any, Iterator

import pytest

from verifier.__main__ import main
from verifier.judge import run_judge
from verifier.processes import ProcessGroups, SHUTDOWN_SIGNALS, Shutdown, run_owned, shutdown_scope
from verifier.sandbox import run_command


class Tree:
    def __init__(self, outcome: str = "timeout", cooperative: bool = False) -> None:
        self.now = 0.0
        self.members = {12345, 12346}
        self.events: list[tuple[int, int]] = []
        self.outcome = outcome
        self.cooperative = cooperative
        self.launches: list[dict[str, Any]] = []
        self.returncode: int | None = None
        self.pid = 12345
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO()
        self.stderr = io.BytesIO()
        self.handlers: dict[int, Any] = {sig: signal.SIG_DFL for sig in SHUTDOWN_SIGNALS}
        self.owner = ProcessGroups(clock=lambda: self.now, kill_group=self.kill, sleep=self.sleep)

    def sleep(self, seconds: float) -> None:
        assert 0 < seconds <= 0.02
        self.now += seconds

    def kill(self, pid: int, sig: int) -> None:
        assert pid == self.pid
        self.events.append((pid, sig))
        if not self.members:
            raise ProcessLookupError
        if sig == signal.SIGKILL or (sig == signal.SIGTERM and self.cooperative):
            self.members.clear()
            self.returncode = -sig

    def set_signal(self, sig: int, handler: Any) -> Any:
        previous = self.handlers[sig]
        self.handlers[sig] = handler
        return previous

    def launch(self, argv: list[str], **kwargs: Any) -> Tree:
        assert kwargs["start_new_session"] is True and kwargs["shell"] is False
        self.launches.append(kwargs)
        return self

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, timeout: float) -> int | None:
        assert timeout <= 0.1
        assert not self.members
        return self.returncode

    def communicate(self, input: str | None, timeout: float) -> tuple[Any, Any]:
        assert timeout <= 9.0
        if self.outcome in {"SIGTERM", "SIGHUP", "SIGINT"}:
            sig = getattr(signal, self.outcome)
            self.handlers[sig](sig, None)
        if self.outcome == "timeout":
            self.now += timeout
            raise subprocess.TimeoutExpired("fake tree", timeout, output=b"partial", stderr=b"err")
        if self.outcome == "error":
            raise OSError("mock pipe error")
        self.returncode = 0
        self.members.discard(self.pid)
        if self.outcome == "already_exited":
            self.members.clear()
        return ("output", "") if self.launches[-1].get("text") else (b"output", b"")


@pytest.mark.parametrize("entry", ["judge", "sandbox"])
@pytest.mark.parametrize("outcome", ["success", "already_exited", "timeout", "error", "SIGTERM", "SIGHUP", "SIGINT"])
def test_owned_tree_cleanup(
    entry: str, outcome: str, workspace: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    tree = Tree(outcome)
    monkeypatch.setattr(subprocess, "Popen", tree.launch)
    monkeypatch.setattr("verifier.processes.time.monotonic", lambda: tree.now)
    monkeypatch.setattr("verifier.sandbox.sys.platform", "darwin")
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    def run() -> Any:
        if entry == "judge":
            return run_judge(["mock"], cwd=workspace, env={}, timeout=9)
        return run_command("python -c 'print(1)'", workspace, timeout=9)

    with shutdown_scope(tree.owner, tree.set_signal):
        if outcome.startswith("SIG"):
            with pytest.raises(Shutdown):
                run()
        elif outcome in {"timeout", "error"} and entry == "judge":
            with pytest.raises(subprocess.TimeoutExpired if outcome == "timeout" else OSError):
                run()
        else:
            result = run()
            if outcome == "timeout":
                assert result.error == "command timed out after 9 seconds"
                assert result.stdout == "partial"
            elif outcome == "error":
                assert "command execution failed" in result.error
            elif entry == "judge":
                assert result.stdout == "output"
    assert not tree.members and not tree.owner.children
    assert tree.stdout.closed and tree.stderr.closed and tree.stdin.closed
    assert 0 <= tree.now - (9 if outcome == "timeout" else 0) <= 2.001
    signals = [sig for _, sig in tree.events if sig]
    if outcome in {"success", "already_exited"}:
        assert signals == [signal.SIGKILL]
    else:
        assert signals == [signal.SIGTERM, signal.SIGKILL]
    assert all(handler == signal.SIG_DFL for handler in tree.handlers.values())


def test_cooperative_child_needs_no_kill(workspace: Path) -> None:
    tree = Tree(cooperative=True)
    with pytest.raises(subprocess.TimeoutExpired):
        run_owned(["mock"], timeout=9, runner=tree.launch, clock=lambda: tree.now,
                  kill_group=tree.kill, sleep=tree.sleep)
    assert not tree.members and tree.now == pytest.approx(9)
    assert [sig for _, sig in tree.events if sig] == [signal.SIGTERM]


def test_multiple_groups_share_one_grace_period() -> None:
    tree = Tree()
    other = Tree()
    other.pid = 22345
    other.members = {22345, 22346}
    def kill(pid: int, sig: int) -> None:
        (tree if pid == tree.pid else other).kill(pid, sig)
    owner = ProcessGroups(clock=lambda: tree.now, kill_group=kill, sleep=tree.sleep)
    owner.children = {tree.pid: tree, other.pid: other}
    owner.cleanup(graceful=True)
    assert not tree.members and not other.members
    assert tree.now == pytest.approx(2.0)


@pytest.mark.parametrize("sig", SHUTDOWN_SIGNALS)
def test_cli_signal_exits_two_without_stdout_or_verdict(
    contract: dict[str, Any], workspace: Path, transcript: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], sig: int,
) -> None:
    tree = Tree(signal.Signals(sig).name)
    path = workspace / "contract.json"
    path.write_text(json.dumps(contract))
    out = workspace / "verdict.json"
    monkeypatch.setattr("verifier.__main__.shutdown_scope", lambda: shutdown_scope(tree.owner, tree.set_signal))
    def check(*args: Any, **kwargs: Any) -> None:
        run_owned(["mock"], timeout=9, runner=tree.launch)
    monkeypatch.setattr("verifier.__main__.check_contract", check)
    assert main(["check", "--contract", str(path), "--workspace", str(workspace),
                 "--transcript", str(transcript), "--attempt", "1", "--out", str(out)]) == 2
    captured = capsys.readouterr()
    assert captured.out == "" and signal.Signals(sig).name in captured.err
    assert not out.exists() and not tree.members


def test_signal_during_launch_is_registered_before_delivery(workspace: Path) -> None:
    tree = Tree()
    def launch(argv: list[str], **kwargs: Any) -> Tree:
        tree.handlers[signal.SIGTERM](signal.SIGTERM, None)
        assert tree.pid not in tree.owner.children
        assert tree.handlers[signal.SIGTERM] != signal.SIG_IGN
        return tree.launch(argv, **kwargs)
    with shutdown_scope(tree.owner, tree.set_signal), pytest.raises(Shutdown):
        run_owned(["mock"], timeout=9, runner=launch)
    assert not tree.members and not tree.owner.children


def test_launch_elapsed_time_is_deducted(workspace: Path) -> None:
    tree = Tree("timeout", cooperative=True)
    slices: list[float] = []
    def launch(argv: list[str], **kwargs: Any) -> Tree:
        tree.now += 0.25
        return tree.launch(argv, **kwargs)
    original = tree.communicate
    def communicate(input: str | None, timeout: float) -> tuple[bytes, bytes]:
        slices.append(timeout)
        return original(input, timeout)
    tree.communicate = communicate  # type: ignore[method-assign]
    with pytest.raises(subprocess.TimeoutExpired) as caught:
        run_owned(["mock"], timeout=9, runner=launch, clock=lambda: tree.now,
                  kill_group=tree.kill, sleep=tree.sleep)
    assert sum(slices) == pytest.approx(8.75)
    assert caught.value.timeout == 9
    assert tree.now == pytest.approx(9) and not tree.members


def test_budget_includes_timeout_tree_cleanup(
    contract: dict[str, Any], workspace: Path, transcript: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from verifier.check import check_contract
    from verifier.schema import validate

    tree = Tree()
    monkeypatch.setenv("HARNESS_VERIFY_BUDGET_SECONDS", "10")
    monkeypatch.setattr(subprocess, "Popen", tree.launch)
    monkeypatch.setattr("verifier.processes.time.monotonic", lambda: tree.now)
    monkeypatch.setattr("verifier.sandbox.sys.platform", "darwin")
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    contract["success_criteria"] = [
        {"id": f"SC-{index}", "description": "Run check", "check": {
            "type": "command", "command": "python -c 'print(1)'", "expected": {"exit_code": 0}}}
        for index in (1, 2)
    ]
    with shutdown_scope(tree.owner, tree.set_signal):
        verdict = check_contract(contract, workspace, transcript, 1, clock=lambda: tree.now)
    validate(verdict, "verdict.schema.json")
    assert len(tree.launches) == 1
    assert not tree.members and tree.now == pytest.approx(10)
    assert verdict["items"][0]["status"] == "unverifiable"
    assert "budget" in verdict["items"][1]["reason"]
    assert verdict["reinstruct_message"]


class ExitingGroupTree(Tree):
    """Model macOS group lookup failing while its known child still needs reaping."""

    def __init__(self, outcome: str, group_errno: int, failing_signal: int | None) -> None:
        super().__init__(outcome)
        self.group_errno = group_errno
        self.failing_signal = failing_signal
        self.direct_signals: list[int] = []
        self.reaped = False
        self.group_errors = 0

    def kill(self, pid: int, sig: int) -> None:
        if self.failing_signal is None or sig == self.failing_signal:
            self.events.append((pid, sig))
            self.group_errors += 1
            # Descendants have exited as the group becomes gone/unsignalable;
            # the direct child can still be alive and require PID fallback.
            self.members.intersection_update({self.pid} if self.returncode is None else set())
            raise OSError(self.group_errno, "injected exiting group")
        super().kill(pid, sig)

    def send_signal(self, sig: int) -> None:
        assert self.poll() is None
        self.direct_signals.append(sig)
        if sig == signal.SIGKILL:
            self.members.discard(self.pid)
            self.returncode = -sig

    def wait(self, timeout: float) -> int | None:
        code = super().wait(timeout)
        self.reaped = True
        return code

    def communicate(self, input: str | None, timeout: float) -> tuple[Any, Any]:
        if self.outcome.startswith("SIG"):
            sig = getattr(signal, self.outcome)
            self.handlers[sig](sig, None)
        if self.outcome == "timeout":
            self.now += timeout
            raise subprocess.TimeoutExpired("fake command", timeout, output=b"partial", stderr=b"err")
        return super().communicate(input, timeout)


@pytest.mark.parametrize("group_errno", [errno.EPERM, errno.ESRCH])
@pytest.mark.parametrize("failing_signal", [signal.SIGTERM, 0, signal.SIGKILL, None])
@pytest.mark.parametrize("outcome", ["timeout", "SIGTERM", "SIGHUP", "SIGINT"])
def test_cli_group_errors_preserve_timeout_or_shutdown(
    group_errno: int, failing_signal: int | None, outcome: str,
    contract: dict[str, Any], workspace: Path, transcript: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    _cli_exiting_group_case(group_errno, failing_signal, outcome, 6, contract,
                            workspace, transcript, monkeypatch, capsys)


@pytest.mark.parametrize("group_errno", [errno.EPERM, errno.ESRCH])
def test_cli_sixty_second_budget_group_race(
    group_errno: int, contract: dict[str, Any], workspace: Path, transcript: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    _cli_exiting_group_case(group_errno, None, "timeout", 60, contract,
                            workspace, transcript, monkeypatch, capsys)


def _cli_exiting_group_case(
    group_errno: int, failing_signal: int | None, outcome: str, budget: int,
    contract: dict[str, Any], workspace: Path, transcript: Path,
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    from verifier.check import check_contract
    from verifier.schema import validate

    tree = ExitingGroupTree(outcome, group_errno, failing_signal)
    monkeypatch.setenv("HARNESS_VERIFY_BUDGET_SECONDS", str(budget))
    monkeypatch.setattr(subprocess, "Popen", tree.launch)
    monkeypatch.setattr("verifier.processes.time.monotonic", lambda: tree.now)
    monkeypatch.setattr("verifier.sandbox.sys.platform", "darwin")
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    def check(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return check_contract(*args, **kwargs, clock=lambda: tree.now)
    monkeypatch.setattr("verifier.__main__.check_contract", check)
    contract["success_criteria"] = [
        {"id": f"SC-{index}", "description": "Run check", "check": {
            "type": "command", "command": "python -c 'print(1)'", "expected": {"exit_code": 0}}}
        for index in (1, 2)
    ]
    path = workspace / "contract.json"
    path.write_text(json.dumps(contract))
    out = workspace / "verdict.json"

    @contextmanager
    def scope() -> Iterator[ProcessGroups]:
        with shutdown_scope(tree.owner, tree.set_signal) as groups:
            yield groups
        # Publication must follow even the last context-manager cleanup pass.
        assert not out.exists()
        assert capsys.readouterr().out == ""
        assert tree.reaped and not tree.owner.children
    monkeypatch.setattr("verifier.__main__.shutdown_scope", scope)
    code = main(["check", "--contract", str(path), "--workspace", str(workspace),
                 "--transcript", str(transcript), "--attempt", "1", "--out", str(out)])
    captured = capsys.readouterr()
    assert tree.group_errors and not tree.members and tree.reaped
    assert not tree.owner.children and len(tree.launches) == 1
    if outcome == "timeout":
        assert code == 0 and captured.out == str(out) + "\n"
        verdict = json.loads(out.read_text())
        validate(verdict, "verdict.schema.json")
        first, second = verdict["items"]
        assert first["status"] == second["status"] == "unverifiable"
        assert first["reason"] == f"command timed out after {budget - 2:g} seconds"
        assert "budget" in second["reason"] and verdict["reinstruct_message"]
        assert "cannot launch" not in json.dumps(verdict)
    else:
        assert code == 2 and captured.out == "" and not out.exists()
        assert outcome in captured.err
    if failing_signal in {signal.SIGTERM, signal.SIGKILL, None}:
        assert tree.direct_signals  # Known child needed fallback at least once.
    assert all(handler == signal.SIG_DFL for handler in tree.handlers.values())


@pytest.mark.parametrize("group_errno", [errno.EPERM, errno.ESRCH])
def test_exited_child_is_reaped_without_direct_signal(group_errno: int) -> None:
    tree = ExitingGroupTree("already_exited", group_errno, signal.SIGKILL)
    result = run_owned(["mock"], timeout=9, runner=tree.launch, clock=lambda: tree.now,
                       kill_group=tree.kill, sleep=tree.sleep)
    assert result.returncode == 0 and tree.reaped
    assert not tree.members and not tree.direct_signals and not tree.owner.children


@pytest.mark.parametrize("direct_errno", [errno.EPERM, errno.ESRCH])
def test_child_exits_during_direct_signal_fallback(direct_errno: int) -> None:
    tree = ExitingGroupTree("timeout", errno.EPERM, None)
    def exited(sig: int) -> None:
        tree.direct_signals.append(sig)
        tree.members.clear()
        tree.returncode = 0
        raise OSError(direct_errno, "injected child exit race")
    tree.send_signal = exited  # type: ignore[method-assign]
    with pytest.raises(subprocess.TimeoutExpired):
        run_owned(["mock"], timeout=9, runner=tree.launch, clock=lambda: tree.now,
                  kill_group=tree.kill, sleep=tree.sleep)
    assert tree.reaped and not tree.members


@pytest.mark.parametrize("group_errno", [errno.EPERM, errno.ESRCH])
def test_judge_timeout_reason_survives_group_error(
    group_errno: int, contract: dict[str, Any], workspace: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from verifier.judge import judge_criterion

    tree = ExitingGroupTree("timeout", group_errno, None)
    monkeypatch.setattr(subprocess, "Popen", tree.launch)
    monkeypatch.setattr("verifier.processes.time.monotonic", lambda: tree.now)
    with shutdown_scope(tree.owner, tree.set_signal):
        result = judge_criterion(contract["success_criteria"][3], workspace, timeout=9)
    assert result.status == "unverifiable"
    assert result.reason == "judge delegation timed out after 9 seconds"
    assert "llm_judge" in result.evidence
    assert tree.reaped and not tree.members and not tree.owner.children


@pytest.mark.parametrize("text", [False, True])
@pytest.mark.parametrize("exit_code", [0, 7])
def test_leader_exit_preserves_result_when_post_kill_drain_never_reaches_eof(
    text: bool, exit_code: int,
) -> None:
    tree = Tree()
    calls: list[float] = []
    def communicate(input: str | None, timeout: float) -> tuple[Any, Any]:
        calls.append(timeout)
        tree.now += timeout
        if len(calls) == 1:
            tree.returncode = exit_code
            tree.members.discard(tree.pid)
        else:
            assert not tree.members  # Group teardown precedes the final drain.
        raise subprocess.TimeoutExpired("held pipe", timeout, output=b"out\r\n", stderr=b"err\r")
    tree.communicate = communicate  # type: ignore[method-assign]
    result = run_owned(["mock"], timeout=120, runner=tree.launch, clock=lambda: tree.now,
                       kill_group=tree.kill, sleep=tree.sleep, text=text)
    assert result.returncode == exit_code
    assert result.stdout == ("out\n" if text else b"out\r\n")
    assert result.stderr == ("err\n" if text else b"err\r")
    assert calls == [0.05, 0.2] and tree.now == pytest.approx(0.25)
    assert not tree.members and tree.stdout.closed and tree.stderr.closed
