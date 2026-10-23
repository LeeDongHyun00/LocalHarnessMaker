from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from verifier.rules import command_rule, evaluate, file_rule, regex_rule
from verifier.sandbox import Execution


@pytest.mark.parametrize(
    ("execution", "expected", "status"),
    [
        (Execution(0, "ok\n"), {"exit_code": 0, "stdout": "ok\n"}, "pass"),
        (Execution(0, "ok\n"), {"exit_code": 0, "stdout": "ok"}, "fail"),
        (Execution(1, "assertion failed"), {"exit_code": 0}, "fail"),
        (Execution(0, "any output"), {"exit_code": 0}, "pass"),
        (Execution(3), {"exit_code": 3}, "pass"),
        (Execution(error="timeout"), {"exit_code": 0}, "unverifiable"),
        (Execution(1, stderr="ModuleNotFoundError: No module named 'fastapi'"), {"exit_code": 1}, "unverifiable"),
        (Execution(4, stderr="ERROR: file or directory not found: test.py"), {"exit_code": 4}, "unverifiable"),
        (Execution(1, stderr="PermissionError: denied"), {"exit_code": 0}, "unverifiable"),
        (Execution(), {"exit_code": 0}, "unverifiable"),
    ],
)
def test_command_status(
    workspace: Path, execution: Execution, expected: dict[str, Any], status: str,
) -> None:
    calls: list[tuple[str, Path, float]] = []

    def runner(command: str, root: Path, timeout: float) -> Execution:
        calls.append((command, root, timeout))
        return execution

    result = command_rule({"type": "command", "command": "fixture check", "expected": expected}, workspace, runner)
    assert result.status == status
    assert calls == [("fixture check", workspace, 120.0)]
    assert "command: fixture check" in result.evidence
    assert f"exit: {execution.exit_code}" in result.evidence


def test_command_evidence_last_fifty_lines(workspace: Path) -> None:
    def runner(command: str, root: Path, timeout: float) -> Execution:
        return Execution(0, "\n".join(f"line {i}" for i in range(75)))

    result = command_rule({"command": "fixture", "expected": {"exit_code": 0}}, workspace, runner)
    assert "\nline 24\n" not in result.evidence
    assert result.evidence.endswith("line 74")
    assert "\nline 25\n" in result.evidence


@pytest.mark.parametrize(("path", "status"), [("report.txt", "pass"), ("missing", "fail"), ("../external", "unverifiable")])
def test_file_status(workspace: Path, path: str, status: str) -> None:
    assert file_rule({"path": path}, workspace).status == status


def test_file_directory_is_not_file(workspace: Path) -> None:
    assert file_rule({"path": "."}, workspace).status == "fail"


@pytest.mark.parametrize(
    ("path", "pattern", "status"),
    [("report.txt", "health ok", "pass"), ("report.txt", "wrong", "fail"),
     ("missing", "ok", "unverifiable"), ("report.txt", "[", "unverifiable"),
     ("../external", ".*", "unverifiable")],
)
def test_regex_status(workspace: Path, path: str, pattern: str, status: str) -> None:
    assert regex_rule({"path": path, "pattern": pattern}, workspace).status == status


def test_regex_evidence_ten_matching_lines(workspace: Path) -> None:
    (workspace / "report.txt").write_text("\n".join(f"ok {i}" for i in range(20)))
    result = regex_rule({"path": "report.txt", "pattern": "ok"}, workspace)
    assert len(result.evidence.splitlines()) == 11
    assert result.evidence.endswith("10: ok 9")


def test_regex_multiline(workspace: Path) -> None:
    result = regex_rule({"path": "report.txt", "pattern": "health ok\\nroute preserved"}, workspace)
    assert result.status == "pass"
    assert "1: health ok\n2: route preserved" in result.evidence


def test_path_symlink_escape(workspace: Path, tmp_path: Path) -> None:
    (workspace / "escape").symlink_to(workspace.parent / "external")
    assert file_rule({"path": "escape"}, workspace).status == "unverifiable"
    assert regex_rule({"path": "escape", "pattern": ".*"}, workspace).status == "unverifiable"


def test_absolute_file_path_rejected(workspace: Path) -> None:
    assert file_rule({"path": str(workspace / "report.txt")}, workspace).status == "unverifiable"


def test_invalid_utf8_regex(workspace: Path) -> None:
    (workspace / "binary").write_bytes(b"\xff")
    assert regex_rule({"path": "binary", "pattern": "."}, workspace).status == "unverifiable"


def test_dispatch_and_unimplemented_judge(workspace: Path) -> None:
    assert evaluate({"type": "file_exists", "path": "report.txt"}, workspace).status == "pass"
    assert evaluate({"type": "regex", "path": "report.txt", "pattern": "ok"}, workspace).status == "pass"
    judge = evaluate({"type": "llm_judge", "rubric": "review"}, workspace)
    assert judge.status == "unverifiable"
    assert "llm_judge" in judge.evidence


@pytest.mark.parametrize("check,cause,reason", [
    ({"type": "regex", "path": "missing", "pattern": "ok"}, "workspace", "workspace regex input"),
    ({"type": "regex", "path": "report.txt", "pattern": "["}, "contract", "contract regex rejected"),
    ({"type": "regex", "path": "../external", "pattern": "."}, "contract", "contract path rejected"),
    ({"type": "file_exists", "path": "../external"}, "contract", "contract path rejected"),
])
def test_mechanical_unverifiable_causes(
    workspace: Path, check: dict[str, Any], cause: str, reason: str,
) -> None:
    result = evaluate(check, workspace)
    assert result.status == "unverifiable" and result.cause.value == cause
    assert reason in result.reason


@pytest.mark.parametrize("execution,cause", [
    (Execution(1, stderr="ModuleNotFoundError: No module named 'app'"), "workspace"),
    (Execution(4, stderr="ERROR: file or directory not found: tests/test_app.py"), "workspace"),
    (Execution(error="sandbox unavailable; command not executed"), "verifier"),
    (Execution(error="command timed out after 120 seconds"), "verifier"),
    (Execution(), "verifier"),
])
def test_command_unverifiable_causes(workspace: Path, execution: Execution, cause: str) -> None:
    result = command_rule({"command": "fixture", "expected": {"exit_code": 0}}, workspace,
                          lambda command, root, timeout: execution)
    assert result.status == "unverifiable" and result.cause.value == cause
