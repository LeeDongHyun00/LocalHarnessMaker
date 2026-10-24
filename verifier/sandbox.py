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
from pathlib import Path, PureWindowsPath
import re
import shlex
import subprocess
import sys
import time
from typing import Protocol

from verifier.causes import Cause
from verifier.processes import LaunchError, run_owned


@dataclass(frozen=True)
class Execution:
    """Captured command outcome, with infrastructure failures kept separate."""

    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    error: str | None = None
    duration: float = 0.0
    cause: Cause = Cause.VERIFIER
    stdout_bytes: bytes | None = None
    stderr_bytes: bytes | None = None


class Runner(Protocol):
    def __call__(self, command: str, workspace: Path, timeout: float) -> Execution: ...


class RejectedCommand(ValueError):
    """A command cannot be safely dispatched by the initial runner."""

    def __init__(self, message: str, cause: Cause = Cause.CONTRACT) -> None:
        super().__init__(message)
        self.cause = cause


_MUTATING_CALLS = {
    "remove", "unlink", "rmdir", "rmtree", "rename", "replace", "truncate",
    "system", "popen", "exec", "eval", "execv", "execve", "spawn", "run",
}


def _input_path(token: str, workspace: Path) -> None:
    path = Path(token)
    if path.is_absolute() or not (workspace / path).resolve().is_relative_to(workspace):
        raise RejectedCommand(f"path outside workspace: {token}")
    if not (workspace / path).is_file() and not (workspace / path).is_dir():
        raise RejectedCommand(f"missing command input path: {token}", Cause.WORKSPACE)


def _unittest_target(token: str, workspace: Path) -> None:
    if "/" in token or "\\" in token or token.endswith(".py"):
        _input_path(token, workspace)
        return
    if not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", token):
        raise RejectedCommand(f"unsupported unittest target: {token}")
    # Resolve the longest local module/package prefix without importing code.
    # Class and method suffixes are names, never filesystem operands.
    parts = token.split(".")
    for length in range(len(parts), 0, -1):
        relative = Path(*parts[:length])
        for candidate in (relative.with_suffix(".py"), relative):
            resolved = (workspace / candidate).resolve()
            if not resolved.is_relative_to(workspace):
                raise RejectedCommand(f"path outside workspace: {token}")
            if resolved.is_file() or resolved.is_dir():
                return
    raise RejectedCommand(f"missing command input path: {token}", Cause.WORKSPACE)


def _test_arguments(module: str, arguments: list[str], workspace: Path) -> None:
    discover = module == "unittest" and bool(arguments) and arguments[0] == "discover"
    tokens = arguments[1:] if discover else arguments
    flags = ({"-v", "-q", "-b", "-f"} if module == "unittest" else
             {"-q", "-v", "-s", "-x", "-rA", "--tb=short", "--disable-warnings"})
    operands = {"-k"} | ({"-s", "-p", "-t"} if discover else set())
    if module == "pytest":
        operands.add("-p")
    index = 0
    positional = 0
    while index < len(tokens):
        token = tokens[index]
        if token in flags:
            index += 1
            continue
        option = token[:2]
        if option in operands:
            if token == option:
                index += 1
                if index >= len(tokens) or tokens[index].startswith("-"):
                    raise RejectedCommand(f"missing command option value: {option}")
                value = tokens[index]
            else:
                value = token[2:]
            if not value:
                raise RejectedCommand(f"missing command option value: {option}")
            if option in {"-s", "-t"}:
                _input_path(value, workspace)
            elif option == "-p":
                if module == "pytest":
                    if value != "no:cacheprovider":
                        raise RejectedCommand(f"unsupported pytest plugin: {value}")
                elif "/" in value or "\\" in value or value in {".", ".."}:
                    raise RejectedCommand(f"discovery pattern must be a filename pattern: {value}")
            # -k consumes an expression/name pattern, not a path.
        elif token.startswith("-"):
            raise RejectedCommand(f"unsupported command option: {token}")
        elif discover:
            # unittest also accepts positional start, pattern and top-level.
            if positional in {0, 2}:
                _input_path(token, workspace)
            elif positional == 1:
                if "/" in token or "\\" in token or token in {".", ".."}:
                    raise RejectedCommand(f"discovery pattern must be a filename pattern: {token}")
            else:
                raise RejectedCommand("too many unittest discover arguments")
            positional += 1
        elif module == "unittest":
            _unittest_target(token, workspace)
        else:
            _input_path(token.split("::", 1)[0], workspace)
        index += 1


def command_argv(command: str, workspace: Path) -> list[str]:
    """Accept direct Python checks only; never interpret a shell program."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>")
        lexer.whitespace_split = True
        lexer.commenters = ""
        argv = list(lexer)
    except ValueError as exc:
        raise RejectedCommand(f"invalid command quoting: {exc}") from exc
    if not argv or argv[0] not in {"python", "python3", sys.executable}:
        raise RejectedCommand("unsupported executable; only direct Python checks are enabled")
    if any(token in {";", "&&", "||", "|", ">", ">>", "<", "&"} for token in argv):
        raise RejectedCommand("shell operators are not supported")
    if len(argv) < 3:
        raise RejectedCommand("expected python -m py_compile/pytest/unittest or python -c CODE")
    if argv[1] == "-m" and argv[2] in {"pytest", "unittest"}:
        _test_arguments(argv[2], argv[3:], workspace.resolve())
    elif argv[1] == "-m" and argv[2] == "py_compile":
        for token in argv[3:]:
            if token.startswith("-"):
                raise RejectedCommand(f"unsupported command option: {token}")
            _input_path(token, workspace.resolve())
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
    except RejectedCommand as exc:
        return Execution(error=f"command rejected: {exc}", cause=exc.cause)
    except (OSError, RuntimeError) as exc:
        return Execution(error=f"command validation failed: {exc}")
    return _run_validated(argv, workspace, workspace, timeout, started)


def run_argv(argv: list[str], workspace: Path, cwd: Path, timeout: float) -> Execution:
    """V3 argv adapter: retain the Python allowlist and workspace boundary."""
    started = time.perf_counter()
    try:
        workspace, cwd = workspace.resolve(), cwd.resolve()
        if not cwd.is_relative_to(workspace) or not cwd.is_dir():
            return Execution(error="command cwd is outside workspace or missing")
        if any(".." in Path(token).parts or ".." in PureWindowsPath(token).parts for token in argv):
            return Execution(error="parent traversal in command argv")
        safe = command_argv(shlex.join(argv), cwd)
    except (ValueError, OSError, RuntimeError) as exc:
        return Execution(error=f"command rejected: {exc}")
    return _run_validated(safe, workspace, cwd, timeout, started)


def _run_validated(
    argv: list[str], workspace: Path, cwd: Path, timeout: float, started: float,
) -> Execution:
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
        try:
            process = run_owned(
                [str(sandbox), "-p", seatbelt_profile(workspace), *argv],
                cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            return Execution(
                stdout=(exc.output or b"").decode("utf-8", errors="replace"),
                stderr=(exc.stderr or b"").decode("utf-8", errors="replace"),
                error=f"command timed out after {timeout:g} seconds",
                duration=time.perf_counter() - started,
                stdout_bytes=exc.output or b"", stderr_bytes=exc.stderr or b"",
            )
        error = None
        decoded_err = process.stderr.decode("utf-8", errors="replace")
        if "sandbox-exec:" in decoded_err or "sandbox_apply:" in decoded_err:
            error = "sandbox setup failed; verification unavailable"
        elif process.returncode is not None and process.returncode < 0:
            error = f"command terminated by signal {-process.returncode}"
        return Execution(
            exit_code=process.returncode,
            stdout=process.stdout.decode("utf-8", errors="replace"), stderr=decoded_err,
            error=error, duration=time.perf_counter() - started,
            stdout_bytes=process.stdout, stderr_bytes=process.stderr,
        )
    except LaunchError as exc:
        return Execution(error=f"cannot launch command: {exc}", duration=time.perf_counter() - started)
    except OSError as exc:
        return Execution(error=f"command execution failed: {exc}", duration=time.perf_counter() - started)
