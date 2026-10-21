from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any

import pytest

from verifier.rules import command_rule
from verifier.sandbox import RejectedCommand, command_argv, run_command, seatbelt_profile


@pytest.mark.parametrize("command", [
    "rm -rf .", "sh -c 'echo safe'", "curl https://example.com", "python script.py",
    "python -m pytest --override-ini=pythonpath=/tmp",
    "python -m pytest /tmp/outside.py", "python -m py_compile ../outside.py",
    "python -c 'import os; os.remove(\"data\")'",
    "python -c 'open(\"/tmp/outside\", \"w\").write(\"bad\")'",
    "python -c 'print(1)' ; rm -rf .", "python -c 'eval(\"print(1)\")'",
    "python -c '", "python", "python -m http.server",
])
def test_dangerous_or_unsupported_command_not_executed(
    workspace: Path, monkeypatch: pytest.MonkeyPatch, command: str,
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("subprocess must not be started")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    execution = run_command(command, workspace)
    assert execution.error is not None
    assert execution.exit_code is None


def test_missing_input_not_executed(workspace: Path) -> None:
    execution = run_command("python -m py_compile missing.py", workspace)
    assert execution.error and "missing command input" in execution.error


def test_command_symlink_escape(workspace: Path) -> None:
    (workspace / "escape.py").symlink_to(workspace.parent / "outside.py")
    with pytest.raises(RejectedCommand, match="outside workspace"):
        command_argv("python -m py_compile escape.py", workspace)


def test_profile_restricts_network_and_writes(workspace: Path) -> None:
    profile = seatbelt_profile(workspace)
    assert "(deny network*)" in profile
    assert "(deny file-write*)" in profile
    assert f"(allow file-write* (subpath {json.dumps(str(workspace))}))" in profile


def test_unsupported_platform_fails_closed(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "unsupported")

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("no unsandboxed fallback")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    assert run_command("python -c 'print(1)'", workspace).error == "sandbox unavailable; command not executed"


def test_launch_error_is_unverifiable(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")

    def unavailable(*args: Any, **kwargs: Any) -> None:
        raise OSError("mock launch failure")

    monkeypatch.setattr(subprocess, "Popen", unavailable)
    monkeypatch.setattr(Path, "is_file", lambda self: True)
    assert "cannot launch" in str(run_command("python -c 'print(1)'", workspace).error)


macos = pytest.mark.skipif(
    sys.platform != "darwin" or bool(os.environ.get("CODEX_SANDBOX")),
    reason="requires host macOS Seatbelt; CODEX_SANDBOX denies nested sandbox-exec (pending host verification)",
)


@macos
def test_real_command_pass_and_failure(workspace: Path) -> None:
    assert run_command("python -c 'print(123)'", workspace).stdout == "123\n"
    failed = run_command("python -c 'assert False'", workspace)
    assert failed.exit_code == 1
    assert failed.error is None


@macos
def test_real_compile_inside_workspace(workspace: Path) -> None:
    (workspace / "module.py").write_text("value = 1\n")
    result = command_rule({"command": "python -m py_compile module.py", "expected": {"exit_code": 0}}, workspace)
    assert result.status == "pass", result.evidence
    assert list((workspace / "__pycache__").glob("module.*.pyc"))


@macos
def test_real_timeout(workspace: Path) -> None:
    execution = run_command("python -c 'import time; time.sleep(5)'", workspace, timeout=0.15)
    assert execution.error == "command timed out after 0.15 seconds"
    assert execution.duration < 3


@macos
def test_real_network_denied(workspace: Path) -> None:
    execution = run_command("python -c 'import socket; socket.create_connection((\"127.0.0.1\", 9), timeout=0.1)'", workspace)
    assert execution.exit_code != 0
    assert "PermissionError" in execution.stderr


@macos
def test_real_dynamic_external_write_denied(workspace: Path, tmp_path_factory: pytest.TempPathFactory) -> None:
    external = tmp_path_factory.mktemp("outside-workspace") / "must-not-exist.txt"
    # Avoid a static absolute path literal to exercise the kernel boundary.
    code = f"p = ''.join(map(chr, {list(map(ord, str(external)))})); open(p, 'w').write('probe')"
    execution = run_command(f"python -c {shlex.quote(code)}", workspace)
    assert execution.exit_code != 0
    assert "PermissionError" in execution.stderr
    assert not external.exists()


@macos
def test_environment_does_not_leak_credentials(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERIFIER_TEST_SECRET", "do-not-forward")
    execution = run_command("python -c 'import os; print(os.environ.get(\"VERIFIER_TEST_SECRET\", \"absent\"))'", workspace)
    assert execution.stdout == "absent\n"
