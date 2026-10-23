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


@pytest.mark.parametrize("arguments", [
    "", "discover -v", "discover -q -b -f -k health",
    "discover -s tests -p 'test_*.py' -t . -v",
    "discover -stests -p'test_*.py' -t. -khealth",
    "discover tests 'test_*.py' .", "-v tests.test_health",
    "tests.test_health.HealthTests", "tests.test_health.HealthTests.test_ok",
    "-q -b -f -k '*ok*' tests/test_health.py", "./tests/test_health.py",
])
def test_unittest_arguments_accepted(workspace: Path, arguments: str) -> None:
    (workspace / "tests").mkdir()
    (workspace / "tests/test_health.py").write_text("import unittest\n")
    command = "python -m unittest " + arguments
    assert command_argv(command, workspace) == [sys.executable, "-m", "unittest", *shlex.split(arguments)]


@pytest.mark.parametrize("arguments", [
    "-x", "-k 'health and not slow'", "-rA --tb=short -p no:cacheprovider",
    "-x -khealth -rA --tb=short -pno:cacheprovider tests/test_health.py::test_ok",
])
def test_pytest_common_options_accepted(workspace: Path, arguments: str) -> None:
    (workspace / "tests").mkdir()
    (workspace / "tests/test_health.py").write_text("def test_ok(): pass\n")
    assert command_argv("python -m pytest " + arguments, workspace) == [
        sys.executable, "-m", "pytest", *shlex.split(arguments)]


@pytest.mark.parametrize("command", [
    "python -m unittest discover -s ../outside", "python -m unittest discover -t /tmp",
    "python -m unittest discover -s/tmp", "python -m unittest discover -t../outside",
    "python -m unittest /tmp/test_health.py", "python -m unittest ../test_health.py",
    "python -m unittest discover -p '../test_*.py'", "python -m unittest discover -p /tmp/test.py",
    "python -m unittest discover . 'test_*.py' ../outside",
    "python -m unittest discover . '../test_*.py'",
    "python -m unittest discover -s", "python -m unittest discover -t",
    "python -m unittest discover -p", "python -m unittest -k",
    "python -m unittest --unknown", "python -m pytest -k", "python -m pytest -p",
    "python -m pytest -p arbitrary_plugin", "python -m pytest --tb=long",
    "python -m unittest discover;echo bad", "python -m unittest discover&&echo bad",
    "python -m unittest discover | python -m unittest", "python -m pytest -k 'x' > report.txt",
])
def test_test_command_rejections_never_launch(
    command: str, workspace: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("rejected command must not launch")
    monkeypatch.setattr("verifier.sandbox.run_owned", forbidden)
    execution = run_command(command, workspace)
    assert execution.error is not None and execution.error.startswith("command rejected:")
    assert execution.exit_code is None


@pytest.mark.parametrize("arguments", ["discover -s escape", "discover -t escape", "escape/test_health.py",
                                         "escape.test_health.HealthTests.test_ok"])
def test_unittest_symlink_escape(workspace: Path, arguments: str) -> None:
    (workspace / "escape").symlink_to(workspace.parent)
    with pytest.raises(RejectedCommand, match="outside workspace"):
        command_argv("python -m unittest " + arguments, workspace)


@pytest.mark.parametrize("arguments", ["discover -s missing", "discover -t missing", "missing.py",
                                         "missing.TestCase.test_ok"])
def test_unittest_missing_input_is_workspace_cause(workspace: Path, arguments: str) -> None:
    from verifier.causes import Cause

    execution = run_command("python -m unittest " + arguments, workspace)
    assert execution.cause == Cause.WORKSPACE
    assert execution.error and "missing command input path" in execution.error


@pytest.mark.parametrize("module", ["unittest discover -v", "pytest -x -k health -rA --tb=short -p no:cacheprovider"])
@pytest.mark.parametrize("exit_code,status", [(0, "pass"), (1, "fail")])
def test_test_commands_use_existing_seatbelt_profile(
    module: str, exit_code: int, status: str, workspace: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    original_is_file = Path.is_file
    monkeypatch.setattr(Path, "is_file", lambda path: str(path) == "/usr/bin/sandbox-exec" or original_is_file(path))
    calls: list[list[str]] = []

    def runner(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        calls.append(argv)
        assert argv[:3] == ["/usr/bin/sandbox-exec", "-p", seatbelt_profile(workspace)]
        assert argv[3:] == [sys.executable, "-m", *shlex.split(module)]
        assert kwargs["cwd"] == workspace and kwargs["env"]["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
        return subprocess.CompletedProcess(argv, exit_code, b"", b"OK\n" if exit_code == 0 else b"FAILED\n")

    monkeypatch.setattr("verifier.sandbox.run_owned", runner)
    result = command_rule({"command": "python -m " + module, "expected": {"exit_code": 0}}, workspace)
    assert result.status == status and len(calls) == 1


@macos
@pytest.mark.parametrize("passing", [True, False], ids=["pass", "fail"])
def test_real_unittest_discover(workspace: Path, passing: bool) -> None:
    tests = workspace / "tests"
    tests.mkdir()
    (tests / "__init__.py").write_text("")
    (tests / "test_health.py").write_text(
        "import unittest\nclass HealthTests(unittest.TestCase):\n"
        f"    def test_ok(self): self.assertTrue({passing!r})\n")
    result = command_rule({"command": "python -m unittest discover -s tests -p 'test_*.py' -t . -v",
                           "expected": {"exit_code": 0}}, workspace)
    assert result.status == ("pass" if passing else "fail"), result.evidence
    assert "Ran 1 test" in result.evidence
    assert ("OK" if passing else "FAILED (failures=1)") in result.evidence
