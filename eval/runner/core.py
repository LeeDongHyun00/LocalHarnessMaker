"""Minimal baseline runner with durable execution segments and private grading."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable
import uuid

from eval.runner import harness
from eval.runner.report import build, build_task
from eval.runner.audit import PrivateGraders, audit_logs, digest, executor_environment
from eval.runner.process import ProcessResult, run_process
from eval.runner.telemetry import collect, records, session_id


REPOSITORY = Path(__file__).resolve().parents[2]


def now() -> str:
    """Return an unambiguous UTC evidence timestamp."""
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: Any) -> None:
    """Replace a checkpoint atomically without deleting previous artifacts."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def load_config(path: Path) -> dict[str, Any]:
    """Accept the JSON subset of YAML without changing root dependencies."""
    config = json.loads(path.read_text())
    required = {"name", "model", "reasoning_effort", "harness", "control_backend", "reinstruction_limit",
                "retry_limit", "seed", "codex_version", "tasks", "timeout_seconds", "grading_timeout_seconds"}
    if not isinstance(config, dict) or set(config) != required:
        raise ValueError("Config must contain exactly the documented baseline fields")
    if type(config["harness"]) is not bool:
        raise ValueError("harness must be boolean")
    if config["harness"]:
        if config["control_backend"] not in {"codex_cli", "cheap_api", "local"}:
            raise ValueError("Harness needs an explicit control backend")
    elif config["control_backend"] != "none" or config["reinstruction_limit"] != 0:
        raise ValueError("Standalone baselines cannot select control orchestration")
    if config["reasoning_effort"] not in {"low", "medium", "high", "xhigh", "max"}:
        raise ValueError("Unsupported reasoning effort")
    for key in ("retry_limit", "reinstruction_limit", "seed"):
        if type(config[key]) is not int or config[key] < 0:
            raise ValueError(f"{key} must be a nonnegative integer")
    for key in ("timeout_seconds", "grading_timeout_seconds"):
        if type(config[key]) not in {int, float} or not 0 < config[key] <= 3600:
            raise ValueError(f"{key} must be in (0, 3600]")
    if not isinstance(config["tasks"], list) or not config["tasks"] or len(set(config["tasks"])) != len(config["tasks"]):
        raise ValueError("Task identifiers must be a nonempty unique list")
    if any(not isinstance(task, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", task) for task in config["tasks"]):
        raise ValueError("Unsafe task identifier")
    if len(config["tasks"]) * ((config["retry_limit"] + 1) * (config["reinstruction_limit"] + 1) + (3 if config["harness"] else 0)) >= 10:
        raise ValueError("STOP-3: batches of 10 or more executor calls require a reported estimate first")
    for key in ("name", "model", "codex_version"):
        if not isinstance(config[key], str) or not config[key]:
            raise ValueError(f"{key} must be a nonempty string")
    return config


def public_files(task: str) -> list[Path]:
    """Hash only version-controlled inputs; generated/untracked files never enter."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", f"eval/tasks/{task}/"],
        cwd=REPOSITORY, capture_output=True, check=True, timeout=10,
    )
    files = [REPOSITORY / os.fsdecode(name) for name in result.stdout.split(b"\0") if name]
    if not files or any(not path.is_file() or path.is_symlink() for path in files):
        raise ValueError("Task requires regular version-controlled public inputs")
    return sorted(files)


def taskset_digest(private_by_task: dict[str, PrivateGraders]) -> str:
    """Fingerprint tracked public inputs and private test contents without locations."""
    hashes = {
        task: {"public": [
            [str(p.relative_to(REPOSITORY / "eval/tasks" / task)), digest(p.read_bytes())]
            for p in public_files(task)
        ], "graders": sorted(digest(p.read_bytes()) for p in private.files)}
        for task, private in private_by_task.items()
    }
    return digest(json.dumps(hashes, sort_keys=True).encode())


def publish(source: Path, destination: Path, private: PrivateGraders) -> None:
    """Retain original logs externally and publish a redacted review copy."""
    if source.is_file():
        destination.write_text(private.redact(source.read_text(errors="replace")))


def grade(
    workspace: Path, private: PrivateGraders, runtime: Path, destination: Path,
    expected: dict[str, Any], timeout: float, execute: Callable[..., ProcessResult],
    *, retention_root: Path | None = None,
) -> dict[str, Any]:
    """Create an independent grading copy only after all executor turns exited."""
    # Retained separately from executor runtimes; every run audits this location.
    retained = retention_root if retention_root is not None else Path(tempfile.gettempdir()) / "lhm-retained-grading"
    retained.mkdir(mode=0o700, exist_ok=True)
    grading = retained / ("grading-" + uuid.uuid4().hex)
    if any(p.is_symlink() for p in workspace.rglob("*")):
        return {"result": "error", "reason": "Executor workspace contains a symlink", "passed_tests": 0, "failed_tests": 0}
    shutil.copytree(workspace, grading, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    copied_at = now()
    for source in private.files:
        if (grading / source.name).exists():
            raise ValueError("Grader filename collision")
        shutil.copy2(source, grading)
    # A trusted isolated unittest loader ignores PYTHONPATH and user site packages.
    # Workspace code remains untrusted; this is correctness grading, not a security sandbox.
    loader = (
        "import sys, unittest; sys.path.insert(0, '.'); "
        "suite = unittest.TestSuite(); "
        "[suite.addTests(unittest.defaultTestLoader.discover('.', pattern=name)) for name in sys.argv[1:]]; "
        "result = unittest.TextTestRunner(verbosity=2).run(suite); "
        "sys.exit(0 if result.wasSuccessful() else 1)"
    )
    result = execute(
        [sys.executable, "-I", "-c", loader, *(source.name for source in private.files)],
        cwd=grading, env={"PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1"}, stdin="",
        stdout=runtime / "grading.stdout", stderr=runtime / "grading.stderr", timeout=timeout,
    )
    text = (runtime / "grading.stdout").read_text(errors="replace") + (runtime / "grading.stderr").read_text(errors="replace")
    destination.write_text(private.redact(text))
    counts = re.findall(r"Ran (\d+) tests?", text)
    count = int(counts[-1]) if counts else 0
    failures = sum(int(n) for n in re.findall(r"(?:failures|errors)=(\d+)", text))
    ok = result.returncode == 0 and not result.timed_out and count == expected["expected_test_count"] and "\nOK\n" in text
    return {"result": "pass" if ok else "error" if result.timed_out or not counts else "fail",
            "copy_path": str(grading), "copied_at": copied_at, "executor_already_exited": True,
            "grader_source_outside_repository": True, "exit_code": result.returncode,
            "timed_out": result.timed_out, "passed_tests": count if ok else max(0, count - failures),
            "failed_tests": failures, "total_tests": count, "log": destination.name}


def audit_roots(runtime: Path) -> tuple[Path, ...]:
    """Cover current legacy copies and all sibling/cross-run executor runtimes."""
    temporary = Path(tempfile.gettempdir())
    return (temporary / "lhm-retained-grading", *runtime.glob("grading-*"),
            *(p for p in temporary.glob("lhm-eval-*") if p != runtime))


class IncompleteRun(RuntimeError):
    """A halted run retains recovery evidence and cannot publish a report."""


class ReportError(RuntimeError):
    """Post-execution accounting/report validation is an internal failure."""


def run(
    config_path: Path, out: Path, private_root: Path, *,
    execute: Callable[..., ProcessResult] = run_process,
    version: str | None = None,
) -> Path:
    """Run or recover baseline tasks without relying on plugin hooks."""
    config = load_config(config_path)
    metadata = {
        task: json.loads((REPOSITORY / "eval/tasks" / task / "meta.json").read_text())
        for task in config["tasks"]
    }
    if any(meta.get("frozen") is not True for meta in metadata.values()):
        raise ValueError("Evaluation requires every selected task to be frozen")
    # Public two-session candidates must not consume a single-session executor run.
    if any(meta["two_session"] for meta in metadata.values()):
        raise ValueError("Two-session execution is pending host-verified handoff orchestration")
    out = out.resolve()
    config_hash = digest(config_path.read_bytes())
    actual_version = version or subprocess.run(
        ["codex", "--version"], capture_output=True, text=True, check=True, timeout=10,
    ).stdout.strip()
    if actual_version != config["codex_version"]:
        raise ValueError("Installed Codex version differs from pinned configuration")
    private_by_task = {task: PrivateGraders.load(private_root, task, REPOSITORY) for task in config["tasks"]}
    task_set_hash = taskset_digest(private_by_task)
    # A private root must never appear in config or public task inputs.
    for task, private in private_by_task.items():
        public = REPOSITORY / "eval/tasks" / task
        for path in [config_path, *public.rglob("*")]:
            if path.is_file() and any(marker in path.read_text(errors="replace") for marker in private.markers()):
                raise ValueError("Public task/config includes a private grader marker")
        if any(p.is_file() for p in (public / "hidden_tests").rglob("*")):
            raise ValueError("Move all repository-local graders outside the repository first")
    out.mkdir(parents=True, exist_ok=True)
    checkpoint = out / "checkpoint.json"
    if checkpoint.exists():
        state = json.loads(checkpoint.read_text())
        if state.get("report_schema") != "evaluation-report-v1":
            raise ValueError("Historical provisional checkpoint requires offline migration; use a fresh output directory")
        if state["config_sha256"] != config_hash:
            raise ValueError("Resume configuration differs from checkpoint")
        if state.get("task_set_sha256") != task_set_hash:
            raise ValueError("Resume task set differs from checkpoint")
    else:
        state = {"report_schema": "evaluation-report-v1", "run_id": uuid.uuid4().hex, "created_at": now(), "config_sha256": config_hash,
                 "task_set_sha256": task_set_hash, "tasks": {}}
        write_json(checkpoint, state)
    order = list(config["tasks"])
    random.Random(config["seed"]).shuffle(order)
    stop_reason: str | None = None
    for task_id in order:
        private = private_by_task[task_id]
        public = REPOSITORY / "eval/tasks" / task_id
        task_out = out / task_id
        task_out.mkdir(exist_ok=True)
        entry = state["tasks"].get(task_id)
        if entry and entry.get("result"):
            continue
        if entry is None:
            runtime = Path(tempfile.mkdtemp(prefix="lhm-eval-"))
            if runtime.is_relative_to(private.root) or runtime.is_relative_to(REPOSITORY):
                raise ValueError("Runtime must be separate from private grader storage and repository")
            workspace = runtime / "workspace"
            shutil.copytree(public / "workspace", workspace)
            codex_home = runtime / "codex-home"
            codex_home.mkdir(mode=0o700)
            original_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
            auth = original_home / "auth.json"
            if not auth.is_file():
                raise ValueError("Existing ChatGPT login is required")
            (codex_home / "auth.json").symlink_to(auth.resolve())
            entry = {"runtime": str(runtime), "phase": "ready", "segments": []}
            state["tasks"][task_id] = entry
            write_json(checkpoint, state)
        runtime = Path(entry["runtime"])
        workspace, codex_home = runtime / "workspace", runtime / "codex-home"
        if entry.get("pid"):
            try:
                os.kill(entry["pid"], 0)
            except ProcessLookupError:
                pass
            else:
                raise ValueError("Prior executor process is still alive; cannot resume or grade")
        # If a runner crashed, retain and audit the old segment before resuming.
        prior = [runtime / segment["events"] for segment in entry["segments"]]
        resumed_id = session_id(prior)
        if prior and entry["phase"] == "running":
            entry["phase"] = "interrupted"
            entry.pop("pid", None)
        if entry["phase"] == "interrupted" and not resumed_id:
            raise ValueError("Interrupted executor did not emit a resumable session id")
        execution_finished = entry["phase"] in {"executed", "grading"}
        if not execution_finished and list(runtime.glob("grading-*")):
            raise ValueError("A grading copy already exists; executor resume is prohibited")
        final_process: ProcessResult | None = None
        if execution_finished and entry["segments"]:
            last = entry["segments"][-1]
            final_process = ProcessResult(last["exit_code"], last.get("timed_out", False))
        interrupted = False
        prior_audit = audit_logs(prior, private, require_completion=False, workspace=workspace, repository=REPOSITORY, grading_roots=audit_roots(runtime)) if prior else None
        blocked = prior_audit is not None and prior_audit["status"] != "clean"
        control_error = entry.get("control_error")
        if config["harness"] and not blocked and not execution_finished and not (runtime / "contract.json").exists():
            try:
                harness.contract(public, runtime, config, repository=REPOSITORY, execute=execute)
            except harness.HarnessError as exc:
                control_error = str(exc)
                entry["control_error"] = control_error
        if config["harness"] and not control_error and (runtime / "contract.json").exists():
            generated = json.loads((runtime / "contract.json").read_text())
            judges = sum(c["check"]["type"] == "llm_judge" for c in generated["success_criteria"])
            maximum_calls = len(config["tasks"]) * (3 + (config["retry_limit"] + 1) *
                (config["reinstruction_limit"] + 1) + 3 * judges * (config["reinstruction_limit"] + 1))
            if maximum_calls >= 10:
                raise ValueError("STOP-3: generated judge criteria require a reported batch cost estimate")
        remaining = (config["retry_limit"] + 1) * (config["reinstruction_limit"] + 1) - len(entry["segments"])
        if not config["harness"]:
            remaining = config["retry_limit"] + 1
        transport_retries = entry.get("transport_retries", 0)
        for retry in range(0 if blocked or execution_finished or control_error else remaining):
            index = len(entry["segments"]) + 1
            event_path, stderr_path = runtime / f"exec-{index}.jsonl", runtime / f"exec-{index}.stderr"
            argv = ["codex", "--no-daemon", "-a", "never", "exec"]
            if resumed_id:
                argv.append("resume")
            argv += ["--ignore-user-config", "--skip-git-repo-check", "--json", "-m", config["model"],
                     "-c", f'model_reasoning_effort="{config["reasoning_effort"]}"',
                     "-c", "features.hooks=false", "-c", "features.plugins=false",
                     "-c", "features.remote_plugin=false", "-c", "mcp_servers={}",
                     "-o", str(runtime / f"final-{index}.md")]
            if resumed_id:
                argv += ["-c", 'sandbox_mode="workspace-write"', resumed_id, "-"]
                prompt = entry.get("reinstruction") or "Continue the original task from the current workspace."
            else:
                argv += ["--sandbox", "workspace-write", "-C", str(workspace), "-"]
                prompt = (public / "prompt.md").read_text()
                if config["harness"]:
                    prompt += "\n\nApproved evaluation contract (benchmark runner authorization):\n" + (runtime / "contract.json").read_text()
            segment = {"attempt": index, "started_at": now(), "events": event_path.name, "stderr": stderr_path.name}
            entry["segments"].append(segment)
            entry["phase"] = "running"
            write_json(checkpoint, state)

            def started(pid: int) -> None:
                entry["pid"] = pid
                write_json(checkpoint, state)

            start = time.monotonic()
            try:
                final_process = execute(
                    argv, cwd=workspace, env=executor_environment(private, codex_home), stdin=prompt,
                    stdout=event_path, stderr=stderr_path, timeout=config["timeout_seconds"], on_start=started,
                )
            except KeyboardInterrupt:
                interrupted = True
                entry["phase"] = "interrupted"
                final_process = ProcessResult(-2)
            segment.update({"exited_at": now(), "exit_code": final_process.returncode,
                            "timed_out": final_process.timed_out, "latency_seconds": time.monotonic() - start})
            entry.pop("pid", None)
            write_json(checkpoint, state)
            current_audit = audit_logs([event_path], private, workspace=workspace, repository=REPOSITORY, grading_roots=audit_roots(runtime))
            if interrupted or current_audit["status"] != "clean":
                break
            resumed_id = session_id([event_path]) or resumed_id
            if final_process.returncode == 0:
                transport_retries = 0
                entry["transport_retries"] = 0
                if not config["harness"]:
                    break
                try:
                    native = sorted((codex_home / "sessions").rglob("*.jsonl"))
                    native_audit = audit_logs(native, private, workspace=workspace, repository=REPOSITORY, grading_roots=audit_roots(runtime))
                    if native_audit["status"] != "clean":
                        break
                    attempt = len(entry.get("verdicts", [])) + 1
                    verdict = harness.verify(runtime, workspace, native, attempt, config,
                                             repository=REPOSITORY, execute=execute)
                    entry.setdefault("verdicts", []).append(verdict)
                    entry["reinstruction"] = verdict["reinstruct_message"]
                    write_json(checkpoint, state)
                    if verdict["overall"] == "pass" or attempt > config["reinstruction_limit"] or not verdict["reinstruct_message"]:
                        break
                    if not resumed_id:
                        raise harness.HarnessError("Verifier continuation needs an executor session ID")
                except harness.HarnessError as exc:
                    control_error = str(exc)
                    entry["control_error"] = control_error
                    break
            else:
                if transport_retries >= config["retry_limit"]:
                    break
                transport_retries += 1
                entry["transport_retries"] = transport_retries
                write_json(checkpoint, state)
        if not interrupted:
            entry["phase"] = "executed"
            write_json(checkpoint, state)
        event_paths = [runtime / segment["events"] for segment in entry["segments"]]
        native_paths = sorted((codex_home / "sessions").rglob("*.jsonl"))
        audit = audit_logs(event_paths + native_paths, private, workspace=workspace, repository=REPOSITORY, grading_roots=audit_roots(runtime))
        telemetry = collect(event_paths, native_paths, config["model"], config["reasoning_effort"])
        # Extract only settings and token/rate-limit evidence from native transcripts.
        selected = [event for path in native_paths for event in records(path)
                    if event.get("type") == "turn_context" or
                    (event.get("type") == "event_msg" and event.get("payload", {}).get("type") == "token_count")]
        (task_out / "session-evidence.jsonl").write_text(private.redact("".join(json.dumps(e) + "\n" for e in selected)))
        for segment, path in zip(entry["segments"], event_paths):
            publish(path, task_out / path.name, private)
            publish(runtime / segment["stderr"], task_out / segment["stderr"], private)
            final = runtime / f'final-{segment["attempt"]}.md'
            if final.exists():
                publish(final, task_out / final.name, private)
        for evidence in runtime.glob("*.json"):
            if evidence.name == "contract.json" or evidence.name.startswith("verdict-"):
                publish(evidence, task_out / evidence.name, private)
        for evidence in [*runtime.glob("contract.std*"), *runtime.glob("verdict-*.std*")]:
            publish(evidence, task_out / evidence.name, private)
        invalid = []
        if control_error:
            invalid.append("control_cli_error")
        if json.loads((public / "meta.json").read_text()).get("two_session"):
            invalid.append("two_session_orchestration_pending")
        if audit["status"] != "clean":
            invalid.append("grader_access_detected" if audit["status"] == "access_detected" else "incomplete_access_audit")
        if not telemetry["settings_evidence"]["verified"]:
            invalid.append("executor_settings_unverified")
        if interrupted:
            invalid.append("execution_interrupted")
        grading = None
        if final_process and final_process.returncode == 0 and not invalid:
            entry["phase"] = "grading"
            write_json(checkpoint, state)
            grading = grade(workspace, private, runtime, task_out / "grading.log",
                            json.loads((public / "expected.json").read_text()),
                            config["grading_timeout_seconds"], execute)
        outcome = "invalid" if invalid else "timeout" if final_process and final_process.timed_out else "error"
        if grading:
            outcome = grading["result"]
        meta = json.loads((public / "meta.json").read_text())
        result = {"task_id": task_id, "task_type": meta["type"], "outcome": outcome,
                  "invalid_reasons": invalid, "attempts": max(1, len(entry["segments"])),
                  "session_id": session_id(event_paths), "segments": entry["segments"],
                  "grader_access_audit": audit, "grading": grading, "verdicts": entry.get("verdicts", []), **telemetry}
        write_json(task_out / "result.json", json.loads(private.redact(json.dumps(result))))
        # Preserve completed source only; no private grader or grading copy is published.
        if grading and not (task_out / "workspace").exists():
            shutil.copytree(workspace, task_out / "workspace", ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        entry["phase"] = "interrupted" if interrupted else "finished"
        if not interrupted:
            entry["result"] = json.loads(private.redact(json.dumps(result)))
        write_json(checkpoint, state)
        if interrupted or (final_process and final_process.returncode != 0):
            stop_reason = "STOP-E1: executor interrupted or could not complete non-interactively; inspect retained logs before another live call."
            break
    tasks = [json.loads((out / task / "result.json").read_text()) for task in order if (out / task / "result.json").exists()]
    attempted = sum(bool(entry.get("segments")) for entry in state["tasks"].values())
    configured = len(config["tasks"])
    write_json(out / "run-diagnostics.json", {
        "stop_reason": stop_reason, "attempted_tasks": attempted, "configured_tasks": configured,
    })
    if stop_reason or {t["task_id"] for t in tasks} != set(config["tasks"]):
        reason = stop_reason or "Incomplete configured task results"
        raise IncompleteRun(f"{reason} Halted after {attempted} of {configured} tasks; "
                            f"attempted={attempted}, configured={configured}")
    pricing = json.loads((REPOSITORY / "eval/prices.yaml").read_text())
    try:
        shared_tasks = [build_task(t, state["tasks"][t["task_id"]], out / t["task_id"], config, pricing,
                                  json.loads((REPOSITORY / "eval/tasks" / t["task_id"] / "meta.json").read_text())) for t in tasks]
        report = build(config, state, shared_tasks, actual_version, REPOSITORY)
    except ValueError as exc:
        raise ReportError("Runtime report accounting or validation failed") from exc
    destination = out / "report.json"
    # Redaction is mandatory even if future report fields unexpectedly contain a private marker.
    text = json.dumps(report, indent=2) + "\n"
    for private in private_by_task.values():
        text = private.redact(text)
    destination.write_text(text)
    return destination
