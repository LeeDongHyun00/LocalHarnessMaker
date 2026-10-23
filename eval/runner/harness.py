"""Hook-independent orchestration through the frozen subprocess CLIs only."""

import json
import os
import re
from pathlib import Path
import sys
from typing import Any, Callable
import uuid

from jsonschema import Draft202012Validator, FormatChecker

from eval.runner.audit import digest
from eval.runner.limits import UsageLimitError, usage_limit_message
from eval.runner.process import ProcessResult


class HarnessError(RuntimeError):
    """A control command failed or returned inconsistent structured output."""

    invalid_reason = "control_cli_error"


class ControlFilePreexisting(HarnessError):
    """An output was present before its trusted producer ran."""

    invalid_reason = "runner_control_file_preexisting"


class ControlFiles:
    """Pin runner-created control bytes; the executor runtime is untrusted storage."""

    def __init__(self, runtime: Path, hashes: dict[str, str], persist: Callable[[], None]) -> None:
        self.runtime = runtime
        self.hashes = hashes
        self.persist = persist

    def safe(self, path: Path) -> bool:
        """Reject links at the file and every parent below the runtime."""
        return (path.is_relative_to(self.runtime) and
                not any(p.is_symlink() for p in (path, *path.parents)
                        if p == self.runtime or p.is_relative_to(self.runtime)))

    def verify(self) -> None:
        """Compare retained inputs with the runner's in-memory manifest before use."""
        for name, expected in self.hashes.items():
            path = self.runtime / name
            if not self.safe(path) or not path.is_file() or digest(path.read_bytes()) != expected:
                raise HarnessError("Runner-owned control evidence changed")

    def fresh(self, path: Path) -> None:
        """Never adopt or overwrite executor-authored outputs, including broken links."""
        self.verify()
        if not self.safe(path) or path.exists() or path.is_symlink():
            raise ControlFilePreexisting("Control output exists before runner writes it")

    def remember(self, path: Path) -> None:
        """Record only a regular file produced by the current trusted operation."""
        if not self.safe(path) or not path.is_file():
            raise HarnessError("Control output is not a regular runner-owned file")
        self.hashes[str(path.relative_to(self.runtime))] = digest(path.read_bytes())
        self.persist()

    def transcript(self, path: Path, paths: list[Path]) -> None:
        """Create an exclusive merged transcript, or verify an already pinned copy."""
        self.verify()
        content = "".join(p.read_text() for p in paths)
        if str(path.relative_to(self.runtime)) in self.hashes:
            if path.read_text() != content:
                raise HarnessError("Retained control transcript differs")
            return
        self.fresh(path)
        with path.open("x") as stream:
            stream.write(content)
        self.remember(path)

    def archive_interruption(self, paths: list[Path]) -> None:
        """Retain interrupted outputs under fresh names so the operation can retry."""
        self.verify()
        archive = self.runtime / "control-interruptions" / uuid.uuid4().hex
        for path in paths:
            if not path.exists():
                continue
            destination = archive / path.relative_to(self.runtime)
            self.fresh(destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            path.rename(destination)
            self.hashes.pop(str(path.relative_to(self.runtime)))
            self.hashes[str(destination.relative_to(self.runtime))] = digest(destination.read_bytes())
        self.persist()


def invoke(module: str, operation: str, arguments: list[str], destination: Path, *,
           repository: Path, timeout: float, execute: Callable[..., ProcessResult],
           overrides: dict[str, str] | None = None,
           guard: ControlFiles) -> dict[str, Any]:
    """Retain streams and validate the CLI path convention and output schema."""
    env = os.environ.copy()
    env["HARNESS_NESTED"] = "1"
    private_root = env.pop("LHM_PRIVATE_GRADERS", None)
    if private_root:
        env = {k: v for k, v in env.items() if private_root not in v}
    env.update(overrides or {})
    streams = destination.with_name("handoff-validation.json") if operation == "validate-handoff" else destination
    stdout = streams.with_suffix(".stdout")
    stderr = streams.with_suffix(".stderr")
    output_args = [] if operation == "validate-handoff" else ["--out", str(destination)]
    guard.verify()
    for path in [stdout, stderr, *([] if operation == "validate-handoff" else [destination])]:
        guard.fresh(path)
    accounting = streams.with_suffix(".control.json")
    guard.fresh(accounting)
    record = {"operation": operation, "exit_code": None, "timed_out": False}
    accounting.write_text(json.dumps(record) + "\n")
    guard.remember(accounting)
    try:
        process = execute([sys.executable, "-m", module, operation, *arguments, *output_args],
                          cwd=repository, env=env, stdin="", stdout=stdout, stderr=stderr, timeout=timeout)
    except (KeyboardInterrupt, OSError):
        interrupted = [stdout, stderr, *([] if operation == "validate-handoff" else [destination])]
        for path in interrupted:
            if path.exists() or path.is_symlink():
                guard.remember(path)
        guard.archive_interruption([accounting, *interrupted])
        raise
    record.update(exit_code=process.returncode, timed_out=process.timed_out)
    accounting.write_text(json.dumps(record) + "\n")
    guard.remember(accounting)
    for path in [stdout, stderr, *([] if operation == "validate-handoff" else [destination])]:
        if path.exists() or path.is_symlink():
            guard.remember(path)
    guard.verify()
    limit = usage_limit_message([stdout, stderr])
    if limit:
        guard.archive_interruption([accounting, stdout, stderr, *([] if operation == "validate-handoff" else [destination])])
        raise UsageLimitError(limit)
    if process.returncode != 0 or process.timed_out:
        raise HarnessError(f"{module} {operation} failed")
    if stdout.read_text() != str(destination) + "\n":
        raise HarnessError("Control CLI returned an unexpected output path")
    schema_name = "handoff" if operation in {"handoff", "validate-handoff"} else "contract" if operation == "contract" else "verdict"
    try:
        value = json.loads(destination.read_text())
        Draft202012Validator(json.loads((repository / f"schemas/{schema_name}.schema.json").read_text()),
                            format_checker=FormatChecker()).validate(value)
    except Exception as exc:
        raise HarnessError("Control CLI returned invalid structured output") from exc
    return value


def contract(public: Path, runtime: Path, config: dict[str, Any], *, repository: Path,
             execute: Callable[..., ProcessResult], prompt_name: str = "prompt.md",
             handoff: Path | None = None, guard: ControlFiles) -> dict[str, Any]:
    """Supply public prompt and an empty case library without private context."""
    cases = runtime / "cases"
    guard.verify()
    if not guard.safe(cases) or (cases.exists() and (not cases.is_dir() or any(cases.iterdir()))):
        raise HarnessError("Control case library is not runner-owned and empty")
    cases.mkdir(exist_ok=True)
    return invoke("controller", "contract", ["--prompt", str(public / prompt_name), "--handoff", str(handoff) if handoff else "none",
                  "--cases", str(cases), "--backend", config["control_backend"]], runtime / "contract.json",
                  repository=repository, timeout=config["timeout_seconds"], execute=execute, guard=guard)


def verify(runtime: Path, workspace: Path, transcript: list[Path], attempt: int,
           config: dict[str, Any], *, repository: Path, execute: Callable[..., ProcessResult],
           guard: ControlFiles) -> dict[str, Any]:
    """Pass only public execution evidence; grader output never enters this loop."""
    merged = runtime / f"transcript-{attempt}.jsonl"
    guard.transcript(merged, transcript)
    verdict = invoke("verifier", "check", ["--contract", str(runtime / "contract.json"),
                     "--workspace", str(workspace), "--transcript", str(merged), "--attempt", str(attempt)],
                     runtime / f"verdict-{attempt}.json", repository=repository,
                     timeout=config["timeout_seconds"], execute=execute,
                     overrides={"HARNESS_BACKEND": config["control_backend"],
                                "HARNESS_MAX_ATTEMPTS": str(config["reinstruction_limit"] + 1)}, guard=guard)
    expected = json.loads((runtime / "contract.json").read_text())["success_criteria"]
    if verdict["attempt"] != attempt or {i["id"] for i in verdict["items"]} != {c["id"] for c in expected} or len(verdict["items"]) != len(expected):
        raise HarnessError("Verdict criterion IDs or attempt differ from contract")
    if (verdict["overall"] == "pass") != all(i["status"] == "pass" for i in verdict["items"]):
        raise HarnessError("Verdict overall disagrees with its items")
    return verdict


def handoff(day1: Path, runtime: Path, transcript: list[Path], config: dict[str, Any], *,
            repository: Path, execute: Callable[..., ProcessResult], guard: ControlFiles) -> None:
    """Generate and validate the day-1 handoff before constructing day 2."""
    merged = day1 / "handoff-transcript.jsonl"
    guard.transcript(merged, transcript)
    guard.verify()
    verdicts = sorted((guard.runtime / name for name in guard.hashes
                       if (guard.runtime / name).parent == day1 and
                       re.fullmatch(r"verdict-[0-9]+\.json", (guard.runtime / name).name)),
                      key=lambda p: int(p.stem.split("-")[-1]))
    if not verdicts:
        raise HarnessError("Day-1 handoff requires a verifier verdict")
    destination = runtime / "handoff.json"
    if str(destination.relative_to(guard.runtime)) not in guard.hashes:
        invoke("controller", "handoff", ["--transcript", str(merged), "--contract", str(day1 / "contract.json"),
               "--verdict", str(verdicts[-1]), "--backend", config["control_backend"]], destination,
               repository=repository, timeout=config["timeout_seconds"], execute=execute, guard=guard)
    validation = destination.with_name("handoff-validation.stdout")
    if str(validation.relative_to(guard.runtime)) not in guard.hashes:
        invoke("verifier", "validate-handoff", ["--handoff", str(destination)], destination,
               repository=repository, timeout=config["timeout_seconds"], execute=execute, guard=guard)
