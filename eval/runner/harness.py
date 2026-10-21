"""Hook-independent orchestration through the frozen subprocess CLIs only."""

import json
import os
from pathlib import Path
import sys
from typing import Any, Callable

from jsonschema import Draft202012Validator, FormatChecker

from eval.runner.process import ProcessResult


class HarnessError(RuntimeError):
    """A control command failed or returned inconsistent structured output."""


def invoke(module: str, operation: str, arguments: list[str], destination: Path, *,
           repository: Path, timeout: float, execute: Callable[..., ProcessResult],
           overrides: dict[str, str] | None = None) -> dict[str, Any]:
    """Retain streams and validate the CLI path convention and output schema."""
    env = os.environ.copy()
    env["HARNESS_NESTED"] = "1"
    private_root = env.pop("LHM_PRIVATE_GRADERS", None)
    if private_root:
        env = {k: v for k, v in env.items() if private_root not in v}
    env.update(overrides or {})
    stdout = destination.with_suffix(".stdout")
    stderr = destination.with_suffix(".stderr")
    process = execute([sys.executable, "-m", module, operation, *arguments, "--out", str(destination)],
                      cwd=repository, env=env, stdin="", stdout=stdout, stderr=stderr, timeout=timeout)
    if process.returncode != 0 or process.timed_out:
        raise HarnessError(f"{module} {operation} failed")
    if stdout.read_text() != str(destination) + "\n":
        raise HarnessError("Control CLI returned an unexpected output path")
    schema_name = "contract" if operation == "contract" else "verdict"
    try:
        value = json.loads(destination.read_text())
        Draft202012Validator(json.loads((repository / f"schemas/{schema_name}.schema.json").read_text()),
                            format_checker=FormatChecker()).validate(value)
    except Exception as exc:
        raise HarnessError("Control CLI returned invalid structured output") from exc
    return value


def contract(public: Path, runtime: Path, config: dict[str, Any], *, repository: Path,
             execute: Callable[..., ProcessResult]) -> dict[str, Any]:
    """Supply public prompt and an empty case library without private context."""
    cases = runtime / "cases"
    cases.mkdir(exist_ok=True)
    return invoke("controller", "contract", ["--prompt", str(public / "prompt.md"), "--handoff", "none",
                  "--cases", str(cases), "--backend", config["control_backend"]], runtime / "contract.json",
                  repository=repository, timeout=config["timeout_seconds"], execute=execute)


def verify(runtime: Path, workspace: Path, transcript: list[Path], attempt: int,
           config: dict[str, Any], *, repository: Path, execute: Callable[..., ProcessResult]) -> dict[str, Any]:
    """Pass only public execution evidence; grader output never enters this loop."""
    merged = runtime / f"transcript-{attempt}.jsonl"
    merged.write_text("".join(p.read_text() for p in transcript))
    verdict = invoke("verifier", "check", ["--contract", str(runtime / "contract.json"),
                     "--workspace", str(workspace), "--transcript", str(merged), "--attempt", str(attempt)],
                     runtime / f"verdict-{attempt}.json", repository=repository,
                     timeout=config["timeout_seconds"], execute=execute,
                     overrides={"HARNESS_BACKEND": config["control_backend"],
                                "HARNESS_MAX_ATTEMPTS": str(config["reinstruction_limit"] + 1)})
    expected = json.loads((runtime / "contract.json").read_text())["success_criteria"]
    if verdict["attempt"] != attempt or {i["id"] for i in verdict["items"]} != {c["id"] for c in expected} or len(verdict["items"]) != len(expected):
        raise HarnessError("Verdict criterion IDs or attempt differ from contract")
    if (verdict["overall"] == "pass") != all(i["status"] == "pass" for i in verdict["items"]):
        raise HarnessError("Verdict overall disagrees with its items")
    return verdict
