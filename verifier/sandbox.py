"""Fail-closed macOS command execution for the initial verifier.

The command filter is defense in depth, not the isolation boundary. Seatbelt
enforces the network and write restrictions for Python and its descendants.
Unsupported platforms never fall back to an unsandboxed subprocess.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import time
from typing import Protocol


@dataclass(frozen=True)
class Execution:
    """Captured command outcome, with infrastructure failures kept separate."""

    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    error: str | None = None
    duration: float = 0.0


class Runner(Protocol):
    def __call__(self, command: str, workspace: Path, timeout: float) -> Execution: ...


class RejectedCommand(ValueError):
    """A command cannot be safely dispatched by the initial runner."""


_MUTATING_CALLS = {
    "remove", "unlink", "rmdir", "rmtree", "rename", "replace", "truncate",
    "system", "popen", "exec", "eval", "execv", "execve", "spawn", "run",
}


def command_argv(command: str, workspace: Path) -> list[str]:
    """Accept direct Python checks only; never interpret a shell program."""
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise RejectedCommand(f"invalid command quoting: {exc}") from exc
    if not argv or argv[0] not in {"python", "python3", sys.executable}:
        raise RejectedCommand("unsupported executable; only direct Python checks are enabled")
    if any(token in {";", "&&", "||", "|", ">", ">>", "<", "&"} for token in argv):
        raise RejectedCommand("shell operators are not supported")
    if len(argv) < 3:
        raise RejectedCommand("expected python -m py_compile/pytest or python -c CODE")
    if argv[1] == "-m" and argv[2] in {"py_compile", "pytest"}:
        for token in argv[3:]:
            if token.startswith("-"):
                if argv[2] != "pytest" or token not in {"-q", "-v", "-s", "--disable-warnings"}:
                    raise RejectedCommand(f"unsupported command option: {token}")
                continue
            path = Path(token.split("::", 1)[0])
            if path.is_absolute() or not (workspace / path).resolve().is_relative_to(workspace):
                raise RejectedCommand(f"path outside workspace: {token}")
            if not (workspace / path).is_file() and not (workspace / path).is_dir():
                raise RejectedCommand(f"missing command input path: {token}")
    elif argv[1] == "-c" and len(argv) == 3:
        try:
            tree = ast.parse(argv[2])
        except SyntaxError as exc:
            raise RejectedCommand(f"invalid Python check: {exc.msg}") from exc
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                if name in _MUTATING_CALLS:
                    raise RejectedCommand(f"destructive or indirect execution call: {name}")
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                # HTTP route strings are valid; absolute filesystem writes are not.
                if re.match(r"/(?:tmp|private|var|Users|home|etc|usr|opt|dev)(?:/|$)", node.value):
                    raise RejectedCommand("absolute filesystem path in Python check")
                if "../" in node.value:
                    raise RejectedCommand("parent traversal in Python check")
    else:
        raise RejectedCommand("unsupported Python invocation")
    return [sys.executable, *argv[1:]]


def seatbelt_profile(workspace: Path) -> str:
    """Allow writes only beneath the canonical workspace; deny all networking."""
    return (
        "(version 1)(allow default)(deny network*)(deny file-write*)"
        f"(allow file-write* (subpath {json.dumps(str(workspace))}))"
        "(deny signal)"
    )


def run_command(command: str, workspace: Path, timeout: float = 120.0) -> Execution:
    """Run a bounded process group, or return an explicit unverifiable error."""
    started = time.perf_counter()
    workspace = workspace.resolve()
    if not workspace.is_dir():
        return Execution(error="workspace is not a directory")
    try:
        argv = command_argv(command, workspace)
    except (RejectedCommand, OSError, RuntimeError) as exc:
        return Execution(error=f"command rejected: {exc}")
    sandbox = Path("/usr/bin/sandbox-exec")
    if sys.platform != "darwin" or not sandbox.is_file():
        return Execution(error="sandbox unavailable; command not executed")
    # Do not hand API credentials or user startup customizations to workspace code.
    environment = {
        "PATH": os.defpath,
        "HOME": str(workspace), "TMPDIR": str(workspace),
        "TMP": str(workspace), "TEMP": str(workspace),
        "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "LC_ALL": "C", "LANG": "C",
    }
    try:
        with subprocess.Popen(
            [str(sandbox), "-p", seatbelt_profile(workspace), *argv],
            cwd=workspace, env=environment, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
        ) as process:
            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
                return Execution(
                    stdout=stdout.decode("utf-8", errors="replace"),
                    stderr=stderr.decode("utf-8", errors="replace"),
                    error=f"command timed out after {timeout:g} seconds",
                    duration=time.perf_counter() - started,
                )
            error = None
            decoded_err = stderr.decode("utf-8", errors="replace")
            if "sandbox-exec:" in decoded_err or "sandbox_apply:" in decoded_err:
                error = "sandbox setup failed; verification unavailable"
            elif process.returncode is not None and process.returncode < 0:
                error = f"command terminated by signal {-process.returncode}"
            return Execution(
                exit_code=process.returncode,
                stdout=stdout.decode("utf-8", errors="replace"), stderr=decoded_err,
                error=error, duration=time.perf_counter() - started,
            )
    except OSError as exc:
        return Execution(error=f"cannot launch command: {exc}", duration=time.perf_counter() - started)
