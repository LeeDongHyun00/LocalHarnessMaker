"""Delegate qualitative checks exclusively through the approved controller CLI."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable

from jsonschema import ValidationError

from verifier.processes import CaptureState, run_owned
from verifier.rules import Result
from verifier.schema import validate


def judge_timeout() -> float:
    """Read the verifier's deadline independently of controller configuration."""
    timeout = float(os.environ.get("HARNESS_JUDGE_TIMEOUT_SECONDS", "120"))
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("HARNESS_JUDGE_TIMEOUT_SECONDS must be finite and positive")
    return timeout


def run_judge(
    argv: list[str], *, cwd: Path, env: dict[str, str], timeout: float,
    runner: Callable[..., subprocess.Popen[str]] | None = None,
    clock: Callable[[], float] | None = None,
    kill_group: Callable[[int, int], None] | None = None,
    capture: CaptureState | None = None,
) -> subprocess.CompletedProcess[str]:
    """Poll controller exit independently of descendant-held pipes, then clean up."""
    return run_owned(
        argv, cwd=cwd, env=env, timeout=timeout, runner=runner, clock=clock,
        kill_group=kill_group, capture=capture, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True,
    )


def _forward_accounting(capture: CaptureState, backend: str, criterion_id: str, outcome: str) -> None:
    """Forward only accounting records, followed by one flushed transport summary."""
    stderr = capture.stderr or ""
    if isinstance(stderr, bytes):
        # TimeoutExpired retains bytes even for text-mode children. A final UTF-8
        # character may be cut off; complete accounting lines still survive.
        stderr = stderr.decode("utf-8", errors="surrogateescape")
    calls = 0
    forwarded = False
    unterminated = False
    for line in stderr.splitlines(keepends=True):
        if line.startswith(("control_call ", "control_cli_events ")):
            sys.stderr.write(line)
            forwarded = True
            calls += line.startswith("control_call ")
            unterminated = not line.endswith(("\n", "\r"))
    if unterminated:
        sys.stderr.write("\n")  # Separate the summary from an unterminated child record.
    if not capture.launched:
        outcome = "not_launched"
    complete = (outcome == "not_launched" and not forwarded) or (
        capture.exited_by_itself and capture.stderr_complete and calls > 0 and outcome != "timeout"
    )
    print("judge_delegation " + json.dumps({
        "accounting_complete": complete, "backend": backend, "criterion_id": criterion_id,
        "forwarded_control_calls": calls, "outcome": outcome,
    }, sort_keys=True, separators=(",", ":")), file=sys.stderr, flush=True)


def judge_criterion(
    criterion: dict[str, Any], artifact: Path, backend: str = "codex_cli", timeout: float | None = None,
) -> Result:
    # Caller errors must be rejected before launching a potentially paid process.
    validate(criterion, "judgment-input.schema.json")
    if backend not in {"codex_cli", "cheap_api", "local"}:
        raise ValueError("HARNESS_BACKEND must be codex_cli, cheap_api or local")
    timeout = judge_timeout() if timeout is None else timeout
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("judge timeout must be finite and positive")
    if not artifact.is_dir():
        raise ValueError("judge artifact must be an existing workspace directory")
    capture = CaptureState()
    outcome = "failed"
    try:
        with tempfile.TemporaryDirectory(prefix="localharness-judge-") as directory:
            source = Path(directory) / "criterion.json"
            output = Path(directory) / "judgment.json"
            source.write_text(json.dumps(criterion, ensure_ascii=False) + "\n", encoding="utf-8")
            completed = run_judge(
                [sys.executable, "-m", "controller", "judge", "--criterion", str(source),
                 "--artifact", str(artifact.resolve()), "--backend", backend, "--out", str(output)],
                cwd=Path(__file__).resolve().parents[1],
                env={**os.environ, "HARNESS_NESTED": "1"}, timeout=timeout, capture=capture,
            )
            # Injected transports may supply only the standard CompletedProcess.
            if not capture.launched:
                capture.launched = True
                capture.exited_by_itself = completed.returncode >= 0
                capture.stderr_complete = True
                capture.stderr = completed.stderr
            if completed.returncode != 0:
                raise RuntimeError(f"controller judge exited {completed.returncode}")
            if completed.stdout != str(output) + "\n":
                raise ValueError("controller judge stdout must contain exactly its output path")
            judgment = json.loads(output.read_text(encoding="utf-8"))
            validate(judgment, "judgment.schema.json")
            if judgment["criterion_id"] != criterion["id"]:
                raise ValueError("judgment criterion_id does not match input")
            if "llm_judge" not in judgment["evidence"]:
                raise ValueError("judgment evidence lacks llm_judge marker")
            usage = judgment["usage"]
            if (usage["input_tokens"] is not None and usage["cached_input_tokens"] is not None
                    and usage["cached_input_tokens"] > usage["input_tokens"]):
                raise ValueError("cached tokens exceed input tokens")
            if usage["usd"] is not None and (
                usage["pricing_ref"] is None or any(usage[key] is None for key in
                                                  ("input_tokens", "cached_input_tokens", "output_tokens"))
            ):
                raise ValueError("judgment cost lacks usage or pricing reference")
            outcome = "completed"
            return Result(judgment["status"], judgment["evidence"], judgment["reason"])
    except subprocess.TimeoutExpired as exc:
        capture.launched = True
        if exc.stderr is not None:
            capture.stderr = exc.stderr
        outcome = "timeout"
        return Result("unverifiable", f"llm_judge: {exc}",
                      f"judge delegation timed out after {timeout:g} seconds")
    except (OSError, ValueError, RuntimeError, ValidationError, subprocess.SubprocessError) as exc:
        # Never turn broken transport/schema/identity into a passing judgment.
        reason = f"judge delegation unavailable: {type(exc).__name__}"
        detail = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
        return Result("unverifiable", f"llm_judge: {detail}", reason)
    finally:
        _forward_accounting(capture, backend, criterion["id"], outcome)
