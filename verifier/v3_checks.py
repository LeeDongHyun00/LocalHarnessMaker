"""Deterministic v3 checks; unavailable execution never permits repair."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Protocol

from verifier.python_identity import signature_snapshot_bytes
from verifier.sandbox import Execution, run_argv
from verifier.v3_io import confined, digest, encoded, snapshot


class ArgvRunner(Protocol):
    def __call__(self, argv: list[str], workspace: Path, cwd: Path, timeout: float) -> Execution: ...


def evaluate_row(
    row: dict[str, Any], workspace: Path, root: Path, round_number: int,
    timeout: float, runner: ArgvRunner = run_argv,
) -> dict[str, Any]:
    check = row["check"]
    label = f"round-{round_number}-{row['id']}"
    evidence: list[dict[str, str]] = []

    def retain(suffix: str, data: bytes, kind: str = "file") -> None:
        evidence.append(snapshot(root, label + "-" + suffix, data, kind))

    def result(status: str, reason: str) -> dict[str, Any]:
        return {"requirement_id": row["id"], "status": status, "reason": reason, "evidence": evidence}

    def read_input(value: str, suffix: str) -> bytes | None:
        path = confined(workspace, value)
        if not path.is_file():
            retain(suffix + "-missing", encoded({"path": value, "exists": path.exists(), "is_file": False}), "check_output")
            return None
        data = path.read_bytes()
        retain(suffix, data)
        return data

    try:
        kind = check["type"]
        if kind == "unavailable":
            return result("unverifiable", check["reason"])
        if kind in {"file_exists", "file_unchanged", "signature_snapshot"}:
            data = read_input(check["path"], "source")
            if data is None:
                return result("fail", "required file is missing or not a regular file")
            if kind == "file_exists":
                return result("pass", "required file exists; exact bytes retained")
            if kind == "signature_snapshot":
                if Path(check["path"]).suffix != ".py":
                    return result("unverifiable", "only Python signature extraction is supported")
                data = signature_snapshot_bytes(data, check["identifiers"])
                retain("signatures", data, "check_output")
            observed = digest(data)
            matched = observed == check["baseline_sha256"]
            return result("pass" if matched else "fail",
                          f"baseline {check['baseline_sha256']}; observed {observed}")
        if kind not in {"command", "input_immutability"}:
            return result("unverifiable", f"unsupported v3 check: {kind}")
        cwd = confined(workspace, check["cwd"])
        if not cwd.is_dir():
            return result("unverifiable", "command cwd is missing")
        before: list[tuple[dict[str, str], bytes | None]] = []
        for index, fixture in enumerate(check.get("inputs", [])):
            before.append((fixture, read_input(fixture["path"], f"input-{index}-before")))
        if any(data is None for _, data in before):
            return result("unverifiable", "input fixture is missing before probe")
        execution = runner(check["argv"], workspace, cwd, timeout)
        out = execution.stdout_bytes if execution.stdout_bytes is not None else execution.stdout.encode()
        err = execution.stderr_bytes if execution.stderr_bytes is not None else execution.stderr.encode()
        retain("stdout", out, "check_output")
        retain("stderr", err, "check_output")
        retain("execution", encoded({"argv": check["argv"], "cwd": check["cwd"],
               "exit_code": execution.exit_code, "expected_exit_code": check["expected_exit_code"],
               "error": execution.error, "timeout_seconds": timeout}), "check_output")
        changed: list[str] = []
        for index, (fixture, data) in enumerate(before):
            after = read_input(fixture["path"], f"input-{index}-after")
            if after is None or digest(after) != fixture["sha256"] or digest(data or b"") != fixture["sha256"]:
                changed.append(fixture["path"])
        output = (out + b"\n" + err).decode("utf-8", errors="replace")
        if execution.error or execution.exit_code is None:
            return result("unverifiable", execution.error or "runner returned no exit code")
        if re.search(r"ModuleNotFoundError:|ImportError:|FileNotFoundError:|PermissionError:|"
                     r"No module named |ERROR: file or directory not found:|can't open file |"
                     r"Traceback \(most recent call last\):", output) and "AssertionError" not in output:
            return result("unverifiable", "command exception, missing dependency/input or denied resource")
        if execution.exit_code < 0:
            return result("unverifiable", "command terminated by signal")
        if changed:
            return result("fail", "input hashes changed: " + ", ".join(changed))
        matched = execution.exit_code == check["expected_exit_code"]
        return result("pass" if matched else "fail",
                      f"expected exit {check['expected_exit_code']}; observed {execution.exit_code}")
    except Exception as exc:
        return result("unverifiable", f"check unavailable: {type(exc).__name__}: {exc}")
