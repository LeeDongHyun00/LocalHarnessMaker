"""Mechanical checks. Missing evidence is never converted to a pass."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Literal

from verifier.sandbox import Execution, Runner, run_command


@dataclass(frozen=True)
class Result:
    status: Literal["pass", "fail", "unverifiable"]
    evidence: str
    reason: str
    command_duration: float = 0.0


def _tail(text: str, count: int) -> str:
    return "\n".join(text.splitlines()[-count:]) or "(empty)"


def command_rule(
    check: dict[str, Any], workspace: Path, runner: Runner = run_command,
    timeout: float = 120.0,
) -> Result:
    execution: Execution = runner(check["command"], workspace, timeout)
    evidence = (
        f"command: {check['command']}\nexit: {execution.exit_code}\n"
        f"stdout (last 50 lines):\n{_tail(execution.stdout, 50)}"
    )
    if execution.stderr:
        evidence += f"\nstderr (last 50 lines):\n{_tail(execution.stderr, 50)}"
    error = execution.error
    if error is None and re.search(
        r"ModuleNotFoundError:|ImportError:|FileNotFoundError:|PermissionError:|"
        r"No module named |ERROR: file or directory not found:|can't open file ",
        execution.stdout + "\n" + execution.stderr,
    ):
        error = "missing dependency/path or denied resource; command cannot verify criterion"
    if execution.exit_code is None and error is None:
        error = "command runner returned no exit code"
    if error is not None:
        return Result("unverifiable", f"{evidence}\nerror: {error}", error, execution.duration)
    expected = check["expected"]
    if execution.exit_code != expected["exit_code"]:
        return Result("fail", evidence, f"expected exit {expected['exit_code']}, got {execution.exit_code}", execution.duration)
    if "stdout" in expected and execution.stdout != expected["stdout"]:
        return Result("fail", evidence, f"stdout differs from exact expected value {expected['stdout']!r}", execution.duration)
    return Result("pass", evidence, "command matched expected result", execution.duration)


def workspace_path(workspace: Path, value: str) -> Path:
    """Reject external paths, including symlink escapes."""
    root = workspace.resolve()
    relative = Path(value)
    if relative.is_absolute():
        raise ValueError("absolute paths are not allowed")
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("path escapes workspace")
    return path


def file_rule(check: dict[str, Any], workspace: Path) -> Result:
    evidence = f"path: {check['path']}"
    try:
        path = workspace_path(workspace, check["path"])
        if not path.exists():
            return Result("fail", evidence, "required file is missing")
        if not path.is_file():
            return Result("fail", evidence, "required path is not a regular file")
        return Result("pass", evidence, "required file exists")
    except (ValueError, OSError, RuntimeError) as exc:
        return Result("unverifiable", evidence, f"cannot inspect path: {exc}")


def regex_rule(check: dict[str, Any], workspace: Path) -> Result:
    evidence = f"path: {check['path']}; pattern: {check['pattern']}"
    try:
        path = workspace_path(workspace, check["path"])
        pattern = re.compile(check["pattern"], re.MULTILINE)
        contents = path.read_text(encoding="utf-8")
        matches = list(pattern.finditer(contents))
        if not matches:
            return Result("fail", evidence, "pattern did not match")
        lines = contents.splitlines()
        matched_lines: dict[int, str] = {}
        for match in matches:
            first = contents.count("\n", 0, match.start())
            last = contents.count("\n", 0, max(match.start(), match.end() - 1))
            for number in range(first, last + 1):
                if number < len(lines):
                    matched_lines[number + 1] = lines[number]
                if len(matched_lines) >= 10:
                    break
            if len(matched_lines) >= 10:
                break
        excerpt = "\n".join(f"{number}: {line}" for number, line in matched_lines.items())
        return Result("pass", f"{evidence}\n{excerpt}" if excerpt else evidence, "pattern matched")
    except (ValueError, OSError, RuntimeError, re.error) as exc:
        return Result("unverifiable", evidence, f"cannot evaluate regex: {exc}")


def evaluate(check: dict[str, Any], workspace: Path, runner: Runner = run_command) -> Result:
    if check["type"] == "command":
        return command_rule(check, workspace, runner)
    if check["type"] == "file_exists":
        return file_rule(check, workspace)
    if check["type"] == "regex":
        return regex_rule(check, workspace)
    return Result("unverifiable", "llm_judge: not run", "judge delegation is not implemented; shared judge interface is unresolved")
