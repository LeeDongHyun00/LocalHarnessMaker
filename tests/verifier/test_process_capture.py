"""Real Python subprocesses verify exit detection without macOS sandbox-exec."""

from __future__ import annotations

import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time
from typing import Any

import pytest

from verifier.judge import run_judge
from verifier.processes import run_owned
from verifier.rules import command_rule
from verifier.sandbox import Execution


def assert_not_running(pid: int) -> None:
    """Check the known descendant PID without sandbox-forbidden process listing."""
    deadline = time.monotonic() + 0.5
    while True:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        if time.monotonic() >= deadline:
            pytest.fail(f"grandchild {pid} still exists after group cleanup")
        time.sleep(0.01)


@pytest.mark.parametrize("entry", ["command", "judge"])
@pytest.mark.parametrize("exit_code", [0, 7])
def test_real_leader_exit_kills_descendant_holding_pipes(
    entry: str, exit_code: int, workspace: Path,
) -> None:
    pid_file = workspace / "grandchild.pid"
    code = (
        "import subprocess, sys; from pathlib import Path; "
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(2)']); "
        f"Path({str(pid_file)!r}).write_text(str(child.pid)); "
        "print('leader stdout', flush=True); print('leader stderr', file=sys.stderr, flush=True); "
        f"sys.exit({exit_code})"
    )
    leaders: list[subprocess.Popen[Any]] = []

    def launch(argv: list[str], **kwargs: Any) -> subprocess.Popen[Any]:
        process = subprocess.Popen(argv, **kwargs)
        leaders.append(process)
        return process

    started = time.monotonic()
    try:
        if entry == "judge":
            result = run_judge([sys.executable, "-c", code], cwd=workspace, env=dict(os.environ),
                               timeout=1, runner=launch)
            assert result.returncode == exit_code
            assert result.stdout == "leader stdout\n" and result.stderr == "leader stderr\n"
        else:
            def runner(command: str, root: Path, timeout: float) -> Execution:
                completed = run_owned(shlex.split(command), cwd=root, timeout=timeout, runner=launch,
                                      stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return Execution(completed.returncode, completed.stdout.decode(), completed.stderr.decode())
            result = command_rule(
                {"command": f"{shlex.quote(sys.executable)} -c {shlex.quote(code)}",
                 "expected": {"exit_code": 0, "stdout": "leader stdout\n"}},
                workspace, runner, timeout=1,
            )
            assert result.status == ("pass" if exit_code == 0 else "fail"), result
            assert "leader stderr" in result.evidence
        assert time.monotonic() - started < 3
        assert leaders and leaders[0].poll() == exit_code
        assert_not_running(int(pid_file.read_text()))
    finally:
        # Bound teardown even if a regression prevents run_owned from cleaning up.
        for leader in leaders:
            try:
                os.killpg(leader.pid, signal.SIGKILL)
            except (PermissionError, ProcessLookupError):
                pass
            leader.wait(timeout=0.5)


@pytest.mark.parametrize("text", [False, True])
def test_real_capture_drains_both_pipes_without_truncation(text: bool, workspace: Path) -> None:
    expected_out = "out ☃\n" * 20000
    expected_err = "err ☃\n" * 20000
    code = "import sys; sys.stdout.write('out ☃\\n' * 20000); sys.stderr.write('err ☃\\n' * 20000)"
    result = run_owned([sys.executable, "-c", code], cwd=workspace, timeout=2,
                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=text, encoding="utf-8" if text else None)
    assert result.returncode == 0
    assert result.stdout == (expected_out if text else expected_out.encode())
    assert result.stderr == (expected_err if text else expected_err.encode())
