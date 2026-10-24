"""Minimal baseline runner with durable execution segments and private grading."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import random
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from time import sleep
from typing import Any, Callable
import uuid

from eval.runner import harness
from eval.runner.publication import checkout_text, control_target, review_bytes, safe_source
from eval.runner.report import build, build_task, current_commit, native_version_reasons
from eval.runner.audit import FingerprintCache, PrivateGraders, audit_logs, audit_retained_logs, interrupted_logs, digest, executor_environment
from eval.runner import transport
from eval.runner.limits import BACKOFF_SECONDS, UsageLimitError, capacity_message, capacity_refusal_without_items, usage_limit_message
from eval.runner.process import ProcessResult, run_process
from eval.runner.telemetry import collect, collect_runs, applied_tier_records, capture_tier, native_token_delta, native_token_totals, native_request_usage, records, session_id, recover_partial_usage


REPOSITORY = Path(__file__).resolve().parents[2]
WORKSPACE_DIGEST_VERSION = 2
WORKSPACE_CACHE_PATTERNS = (
    "__pycache__", "*.pyc", "*.pyo", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".hypothesis",
)
WORKSPACE_COPY_IGNORE = shutil.ignore_patterns(*WORKSPACE_CACHE_PATTERNS)


def now() -> str:
    """Return an unambiguous UTC evidence timestamp."""
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: Any) -> None:
    """Replace a checkpoint atomically without deleting previous artifacts."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(checkout_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n"))
    temporary.replace(path)


def workspace_digest(workspace: Path, version: int = WORKSPACE_DIGEST_VERSION) -> str:
    """Hash retained paths, contents, modes and links; v2 excludes generated caches."""
    if type(version) is not int or version not in (1, 2):
        raise ValueError("Unsupported workspace digest version")
    if not workspace.is_dir() or workspace.is_symlink():
        raise ValueError("Retained workspace is unavailable")
    if version == 1:
        paths = sorted(workspace.rglob("*"))
    else:
        paths = []

        def unreadable(error: OSError) -> None:
            raise error

        for directory, directories, files in os.walk(workspace, followlinks=False, onerror=unreadable):
            ignored = WORKSPACE_COPY_IGNORE(directory, directories + files)
            directories[:] = [name for name in directories if name not in ignored]
            paths.extend(Path(directory) / name for name in directories + files if name not in ignored)
        paths.sort()
    manifest = []
    for path in paths:
        info = path.lstat()
        kind = ("link" if stat.S_ISLNK(info.st_mode) else "file" if stat.S_ISREG(info.st_mode)
                else "directory" if stat.S_ISDIR(info.st_mode) else None)
        if kind is None:
            raise ValueError("Unsupported retained workspace entry")
        content = os.readlink(path) if kind == "link" else digest(path.read_bytes()) if kind == "file" else None
        manifest.append([path.relative_to(workspace).as_posix(), kind, stat.S_IMODE(info.st_mode), content])
    return digest(json.dumps(manifest, ensure_ascii=True, separators=(",", ":")).encode())


def matching_workspace_digest_version(workspace: Path, recorded: dict[str, Any]) -> int | None:
    """Match a retained pin without changing it; unversioned pins may use v1 or v2."""
    expected = recorded.get("workspace_exit_sha256")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        return None
    versions = (recorded["workspace_digest_version"],) if "workspace_digest_version" in recorded else (1, 2)
    for version in versions:
        if type(version) is not int or version not in (1, 2):
            return None
        if workspace_digest(workspace, version) == expected:
            return version
    return None


def record_workspace_exit(workspace: Path, entry: dict[str, Any], segment: dict[str, Any]) -> None:
    """Pin current workspace bytes; recovery snapshots carry separate provenance."""
    value = workspace_digest(workspace)
    for record in (entry, segment):
        record.update(workspace_exit_sha256=value, workspace_digest_version=WORKSPACE_DIGEST_VERSION)


def valid_day2_observation(entry: dict[str, Any], public: Path) -> bool:
    """Require retained bytes of the exact initial day-2 prompt and both exits."""
    observation = entry.get("day2_observation")
    if not isinstance(observation, dict):
        return False
    try:
        segment = next(s for s in entry["segments"] if s["attempt"] == observation["attempt"])
        day1 = [s for s in entry["segments"] if s.get("day", 1) == 1]
        return (bool(day1) and segment.get("day") == 2 and
                session_id([Path(entry["runtime"]) / segment["events"]]) is not None and
                session_id([Path(entry["runtime"]) / segment["events"]]) not in
                {session_id([Path(entry["runtime"]) / s["events"]]) for s in day1} and
                all(re.fullmatch(r"[0-9a-f]{64}", s.get("workspace_exit_sha256", ""))
                    for s in [*day1, segment]) and
                digest(Path(observation["prompt_path"]).read_bytes()) ==
                observation["delivered_sha256"] == observation["public_sha256"] ==
                digest((public / "day2.md").read_bytes()))
    except (KeyError, OSError, StopIteration, TypeError):
        return False


def load_config(path: Path) -> dict[str, Any]:
    """Accept the JSON subset of YAML without changing root dependencies."""
    config = json.loads(path.read_text())
    required = {"name", "model", "reasoning_effort", "harness", "control_backend", "reinstruction_limit",
                "retry_limit", "seed", "codex_version", "tasks", "timeout_seconds", "grading_timeout_seconds"}
    if not isinstance(config, dict) or set(config) - {"task_timeout_seconds", "static_template_dir", "task_population", "task_root", "service_tier", "calibration"} != required:
        raise ValueError("Config must contain exactly the documented baseline fields")
    if type(config.get("calibration", False)) is not bool:
        raise ValueError("calibration must be boolean")
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
    population = config.get("task_population", config["tasks"])
    if (not isinstance(population, list) or not population or
            any(not isinstance(t, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", t) for t in population) or
            len(set(population)) != len(population) or not set(config["tasks"]).issubset(population)):
        raise ValueError("Task population must uniquely contain all selected task IDs")
    timeouts = config.get("task_timeout_seconds", {})
    if (not isinstance(timeouts, dict) or set(timeouts) - set(config["tasks"]) or
            any(type(v) not in {int, float} or not 0 < v <= 3600 for v in timeouts.values())):
        raise ValueError("Per-task timeouts must select configured tasks and be in (0, 3600]")
    if "static_template_dir" in config:
        if (config["harness"] or config["control_backend"] != "none" or
                not isinstance(config["static_template_dir"], str) or not config["static_template_dir"]):
            raise ValueError("Static templates require a standalone baseline and a directory")
    task_directory(config)
    if "service_tier" in config and (not isinstance(config["service_tier"], str) or
            not re.fullmatch(r"[a-z][a-z0-9_-]*", config["service_tier"])):
        raise ValueError("service_tier must be a nonempty tier identifier")
    require_call_estimate(config)
    for key in ("name", "model", "codex_version"):
        if not isinstance(config[key], str) or not config[key]:
            raise ValueError(f"{key} must be a nonempty string")
    return config


def task_directory(config: dict[str, Any]) -> Path:
    """Resolve a canonical public task root inside eval, without aliases or traversal."""
    root = config.get("task_root", "eval/tasks")
    if (not isinstance(root, str) or not re.fullmatch(r"eval/[a-z0-9][a-z0-9-]*", root)
            or (REPOSITORY / root).is_symlink()
            or not (REPOSITORY / root).resolve().is_relative_to((REPOSITORY / "eval").resolve())):
        raise ValueError("task_root must be a canonical public directory under eval")
    return REPOSITORY / root


def configured_digest(private_by_task: dict[str, PrivateGraders], config: dict[str, Any]) -> str:
    """Keep the historical v1 digest byte-for-byte compatible."""
    root = config.get("task_root", "eval/tasks")
    return taskset_digest(private_by_task) if root == "eval/tasks" else taskset_digest(private_by_task, root)


def paid_call_bound(config: dict[str, Any], judges: dict[str, int] | None = None) -> int:
    """Count both days, transport retries, three-call control budgets and handoffs."""
    two = sum((task_directory(config) / task / "day2.md").is_file() for task in config["tasks"])
    sessions = len(config["tasks"]) + two
    turns = config["reinstruction_limit"] + 1
    executor = sessions * (config["retry_limit"] + 1) * turns
    return executor + (3 * (sessions + two + sum((judges or {}).values()) * turns)
                       if config["harness"] else 0)


def require_call_estimate(config: dict[str, Any], judges: dict[str, int] | None = None, *,
                          recovery: bool = False) -> dict[str, Any]:
    """Require exact estimates, allowing task subsets only for explicit recovery."""
    maximum = paid_call_bound(config, judges)
    if config["harness"]:
        print(f"Paid-call estimate: at most {maximum} calls with currently known judge criteria; "
              "includes both days, contracts, handoff, retries and fallbacks. "
              "New judge criteria require a revised bound; planning USD is in the matched estimate, measured USD requires complete accounting.", file=sys.stderr)
    estimated = [(REPOSITORY / f"eval/configs/{kind}-{letter}.yaml",
                  REPOSITORY / f"eval/reports/{kind}-estimate.md")
                 for kind in ("pilot", "full") for letter in ("a", "b")]
    name = config.get("name", "")
    if isinstance(name, str) and re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
        estimated.insert(0, (REPOSITORY / f"eval/configs/{name}.yaml",
                             REPOSITORY / f"eval/reports/{name}-estimate.md"))
    match = None
    subset = False
    for candidate, estimate in estimated:
        if not candidate.is_file() or not estimate.is_file():
            continue
        approved = json.loads(candidate.read_text())
        subset = (recovery and
                  {k: v for k, v in approved.items() if k != "tasks"} ==
                  {k: v for k, v in config.items() if k != "tasks"} and
                  set(config["tasks"]).issubset(approved["tasks"]))
        if approved == config or subset:
            match = estimate
            break
    if match is None and maximum >= 10:
        raise ValueError(f"STOP-3: batch upper bound {maximum} paid calls requires a reported cost estimate")
    matched_path = str(match.relative_to(REPOSITORY)) if match else None
    if match is not None:
        note = " recovery subset of an approved configuration;" if subset else ""
        print(f"STOP-3 estimate: {matched_path}; batch upper bound {maximum} paid calls;{note} "
              "host operator must obtain user approval before execution.", file=sys.stderr)
    return {"matched_estimate": matched_path, "paid_call_bound": maximum,
            "recovery_subset": bool(match and subset)}


def installed_version() -> str:
    """Read the installed CLI before every executor session; never launch a model."""
    return subprocess.run(["codex", "--version"], capture_output=True, text=True,
                          check=True, timeout=10).stdout.strip()


def public_files(task: str, task_root: str = "eval/tasks") -> list[Path]:
    """Hash only version-controlled inputs; generated/untracked files never enter."""
    task_directory({"task_root": task_root})
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", f"{task_root}/{task}/"],
        cwd=REPOSITORY, capture_output=True, check=True, timeout=10,
    )
    files = [REPOSITORY / os.fsdecode(name) for name in result.stdout.split(b"\0") if name]
    if not files or any(not path.is_file() or path.is_symlink() for path in files):
        raise ValueError("Task requires regular version-controlled public inputs")
    return sorted(files)


def taskset_digest(private_by_task: dict[str, PrivateGraders], task_root: str = "eval/tasks") -> str:
    """Fingerprint tracked public inputs and private test contents without locations."""
    hashes = {
        task: {"public": [
            [str(p.relative_to(REPOSITORY / task_root / task)), digest(p.read_bytes())]
            for p in (public_files(task) if task_root == "eval/tasks" else public_files(task, task_root))
        ], "graders": sorted(digest(p.read_bytes()) for p in private.files)}
        for task, private in private_by_task.items()
    }
    payload = hashes if task_root == "eval/tasks" else {"task_root": task_root, "tasks": hashes}
    return digest(json.dumps(payload, sort_keys=True).encode())


def publish(source: Path, destination: Path, private: PrivateGraders, *, source_root: Path | None = None) -> None:
    """Retain original logs externally and publish a redacted review copy."""
    if source.is_file() and safe_source(source, source_root if source_root is not None else source.parent):
        destination.write_bytes(review_bytes(source.read_bytes(), private))


def grading_summary(text: str) -> str:
    """Publish unittest identifiers/status and totals, never tracebacks or messages."""
    lines = []
    for line in text.splitlines():
        test = re.fullmatch(r"([\w.]+ \([\w.]+\)) \.\.\. (ok|FAIL|ERROR|skipped)(?: .*)?", line)
        if test:
            lines.append(f"{test[1]} ... {test[2]}")
        elif re.fullmatch(r"Ran \d+ tests? in [0-9.]+s|OK(?: \([a-zA-Z ]+=\d+(?:, [a-zA-Z ]+=\d+)*\))?|FAILED \([a-zA-Z ]+=\d+(?:, [a-zA-Z ]+=\d+)*\)", line):
            lines.append(line)
    return "\n".join(lines) + ("\n" if lines else "")


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
    shutil.copytree(workspace, grading, ignore=WORKSPACE_COPY_IGNORE)
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
    (runtime / "grading.log").write_text(text)
    destination.write_text(private.redact(grading_summary(text)))
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
    temporary, runtime = Path(tempfile.gettempdir()).resolve(), runtime.resolve()
    siblings = (p.resolve() for p in temporary.glob("lhm-eval-*"))
    return (temporary / "lhm-retained-grading", *(p.resolve() for p in runtime.glob("grading-*")),
            *(p for p in siblings if p != runtime))


class IncompleteRun(RuntimeError):
    """A halted run retains recovery evidence and cannot publish a report."""


class ReportError(RuntimeError):
    """Post-execution accounting/report validation is an internal failure."""


def run(
    config_path: Path, out: Path, private_root: Path, *,
    execute: Callable[..., ProcessResult] = run_process,
    version: str | Callable[[], str] | None = None,
    _recorded_config_sha256: str | None = None,
) -> Path:
    """Run or recover baseline tasks without relying on plugin hooks."""
    config = load_config(config_path)
    from eval.runner.static_templates import load_templates
    templates = load_templates(config, REPOSITORY)
    template_hashes = {task: digest(content) for task, content in templates.items()}
    metadata = {
        task: json.loads((task_directory(config) / task / "meta.json").read_text())
        for task in config["tasks"]
    }
    if not config.get("calibration", False) and any(meta.get("frozen") is not True for meta in metadata.values()):
        raise ValueError("Evaluation requires every selected task to be frozen")
    if config.get("calibration", False):
        print("Calibration evidence only; this report is not a headline result.", file=sys.stderr)
    out = out.resolve()
    config_hash = _recorded_config_sha256 or digest(config_path.read_bytes())
    version_reader = version if callable(version) else (lambda: version) if version else installed_version
    actual_version = version_reader()
    if actual_version != config["codex_version"]:
        if (out / "checkpoint.json").exists():
            raise IncompleteRun("Codex version changed; run is resumable only with its recorded version")
        raise ValueError("Installed Codex version differs from pinned configuration")
    private_by_task = {task: PrivateGraders.load(private_root, task, REPOSITORY, task_root=config.get("task_root")) for task in config["tasks"]}
    fingerprint_cache = FingerprintCache()
    selected_hash = configured_digest(private_by_task, config)
    population = dict(private_by_task)
    for task in config.get("task_population", []):
        if task not in population:
            meta = json.loads((task_directory(config) / task / "meta.json").read_text())
            if not config.get("calibration", False) and meta.get("frozen") is not True:
                raise ValueError("Population includes unfrozen task")
            population[task] = PrivateGraders.load(private_root, task, REPOSITORY, task_root=config.get("task_root"))
    task_set_hash = configured_digest(population, config) if "task_population" in config else selected_hash
    # A private root must never appear in config or public task inputs.
    for task, private in private_by_task.items():
        public = task_directory(config) / task
        for path in [config_path, *public.rglob("*")]:
            if path.is_file() and any(marker in path.read_text(errors="replace") for marker in private.markers()):
                raise ValueError("Public task/config includes a private grader marker")
        if any(p.is_file() for p in (public / "hidden_tests").rglob("*")):
            raise ValueError("Move all repository-local graders outside the repository first")
    out.mkdir(parents=True, exist_ok=True)
    checkpoint = out / "checkpoint.json"
    if checkpoint.exists():
        state = json.loads(checkpoint.read_text())
        if state.get("report_schema") not in {"evaluation-report-v1", "evaluation-report-v2"}:
            raise ValueError("Historical provisional checkpoint requires offline migration; use a fresh output directory")
        if state.get("pricing_catalog_sha256") is not None and state["pricing_catalog_sha256"] != digest((REPOSITORY / "eval/prices.yaml").read_bytes()):
            raise ValueError("Resume pricing catalog differs from checkpoint")
        if state.get("static_templates", {}) != template_hashes:
            raise ValueError("Static templates changed since run start")
        if state["config_sha256"] != config_hash or state.get("config") != config:
            raise ValueError("Resume configuration differs from checkpoint")
        if state.get("selected_task_set_sha256", selected_hash) != selected_hash:
            raise ValueError("Resume selected inputs differ from checkpoint")
        if state.get("task_set_sha256") != task_set_hash:
            raise ValueError("Resume task set differs from checkpoint")
    else:
        if _recorded_config_sha256 is not None:
            raise ValueError("Recorded configuration requires an existing checkpoint")
        state = {"report_schema": "evaluation-report-v2", "calibration": config.get("calibration", False), "run_id": uuid.uuid4().hex, "created_at": now(), "config_sha256": config_hash,
                 "task_set_sha256": task_set_hash, "config": config, "tasks": {},
                 "static_templates": template_hashes, "selected_task_set_sha256": selected_hash,
                 "git_commit": current_commit(REPOSITORY),
                 "pricing_snapshot_id": json.loads((REPOSITORY / "eval/prices.yaml").read_text())["snapshot_id"],
                 "pricing_catalog_sha256": digest((REPOSITORY / "eval/prices.yaml").read_bytes())}
        write_json(checkpoint, state)
    # A recovery wrapper may have just regraded completed tasks. Keep their
    # accounting and artifacts intact while the normal loop runs fresh tasks;
    # rebuilding them would reprice history and overwrite hash-pinned evidence.
    retained_tasks: dict[str, Any] = {}
    if (out / "report.json").is_file():
        prior_report = json.loads((out / "report.json").read_text())
        retained_tasks = {task["task_id"]: task for task in prior_report["tasks"]
                          if state["tasks"].get(task["task_id"], {}).get("result")}
        from eval.runner.pricing import retained_provenance
        for task in retained_tasks.values():
            retained_provenance(task, prior_report["metadata"]["pricing"])
    order = list(config["tasks"])
    random.Random(config["seed"]).shuffle(order)
    stop_reason: str | None = None
    for task_id in order:
        private = private_by_task[task_id]
        public = task_directory(config) / task_id
        task_out = out / task_id
        task_out.mkdir(exist_ok=True)
        if task_id in templates:
            retained = task_out / "static-template.md"
            if retained.exists() and retained.read_bytes() != templates[task_id]:
                raise ValueError("Retained static template changed")
            retained.write_bytes(templates[task_id])
        entry = state["tasks"].get(task_id)
        if entry and entry.get("result"):
            continue
        if entry is None:
            runtime = Path(tempfile.mkdtemp(prefix="lhm-eval-"))
            if (runtime.resolve().is_relative_to(private.root.resolve()) or
                    runtime.resolve().is_relative_to(REPOSITORY.resolve())):
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
            if task_id in state.get("fresh_reruns", {}):
                entry["rerun_history"] = state["fresh_reruns"][task_id]
            state["tasks"][task_id] = entry
            write_json(checkpoint, state)
        runtime = Path(entry["runtime"])
        workspace, codex_home = runtime / "workspace", runtime / "codex-home"
        def audit(paths: list[Path], private: PrivateGraders, **kwargs: Any) -> dict[str, Any]:
            return audit_retained_logs(paths, private, retained_context=entry.get("retained_audit_context"),
                                       interrupted_paths=interrupted_logs(runtime, entry["segments"]),
                                       _audit=audit_logs, **kwargs)
        guard = harness.ControlFiles(runtime, entry.setdefault("control_files", {}),
                                     lambda: write_json(checkpoint, state))
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
        if entry["phase"] == "interrupted":
            # A hard runner crash may leave only the pre-launch checkpoint. Preserve
            # the incomplete stream and do not invent a successful historical exit.
            for segment in entry["segments"]:
                if "exit_code" not in segment:
                    segment.update(exit_code=-2, exited_at=now(), interrupted=True)
            recover_partial_usage(entry["segments"], sorted((codex_home / "sessions").rglob("*.jsonl")))
            write_json(checkpoint, state)
            if not resumed_id:
                raise IncompleteRun("Interrupted executor has no resumable session id; retained evidence requires host review")
        execution_finished = entry["phase"] in {"executed", "grading"}
        if not execution_finished and list(runtime.glob("grading-*")):
            raise ValueError("A grading copy already exists; executor resume is prohibited")
        final_process: ProcessResult | None = None
        if execution_finished and entry["segments"]:
            last = entry["segments"][-1]
            final_process = ProcessResult(last["exit_code"], last.get("timed_out", False))
        interrupted = False
        infrastructure_stop: str | None = None
        prior_audit = audit(prior, private, require_completion=False, workspace=workspace, repository=REPOSITORY, grading_roots=audit_roots(runtime), fingerprint_cache=fingerprint_cache) if prior else None
        blocked = prior_audit is not None and prior_audit["status"] != "clean"
        two_session = metadata[task_id]["two_session"]
        control_error = entry.get("control_error")
        for day in range(entry.get("active_day", 1), (2 if two_session else 1) + 1):
            entry["active_day"] = day
            control_runtime = runtime / f"day-{day}" if two_session else runtime
            if not guard.safe(control_runtime):
                entry["control_invalid_reason"] = "runner_control_file_preexisting"
                entry["control_error"] = "Control directory is a symlink"
                control_error = entry["control_error"]
                break
            control_runtime.mkdir(exist_ok=True)
            day_segments = [s for s in entry["segments"] if s.get("day", 1) == day]
            day_paths = [runtime / s["events"] for s in day_segments]
            resumed_id = session_id(day_paths)
            current_audit = audit(day_paths, private, workspace=workspace, repository=REPOSITORY,
                                       grading_roots=audit_roots(runtime), fingerprint_cache=fingerprint_cache) if day_paths else None
            day_finished = execution_finished or day in entry.get("completed_days", [])
            if day_segments:
                last = day_segments[-1]
                final_process = ProcessResult(last["exit_code"], last.get("timed_out", False))
            control_error = entry.get("control_error")
            if config["harness"] and not blocked and not execution_finished:
                try:
                    if not entry["segments"]:
                        guard.recover_prelaunch(control_runtime, REPOSITORY)
                    guard.verify()
                except harness.HarnessError as exc:
                    entry["control_invalid_reason"] = exc.invalid_reason
                    control_error = entry["control_error"] = str(exc)
            contract_name = str((control_runtime / "contract.json").relative_to(runtime))
            if config["harness"] and not blocked and not control_error and not execution_finished and contract_name not in guard.hashes:
                try:
                    harness.contract(public, control_runtime, config, repository=REPOSITORY, execute=execute,
                                     prompt_name="day2.md" if day == 2 else "prompt.md",
                                     handoff=runtime / "handoff.json" if day == 2 else None, guard=guard)
                    write_json(checkpoint, state)
                except UsageLimitError as exc:
                    infrastructure_stop = str(exc)
                    break
                except harness.HarnessError as exc:
                    entry["control_invalid_reason"] = exc.invalid_reason
                    control_error = str(exc)
                    entry["control_error"] = control_error
            if config["harness"] and not control_error and (control_runtime / "contract.json").exists():
                generated = json.loads((control_runtime / "contract.json").read_text())
                judges = sum(c["check"]["type"] == "llm_judge" for c in generated["success_criteria"])
                entry.setdefault("judge_counts", {})[f"{task_id}:{day}"] = judges
                require_call_estimate(config, {key: count for task in state["tasks"].values()
                                               for key, count in task.get("judge_counts", {}).items()})

            def verify_executor() -> bool:
                """Checkpoint a pending verifier call separately from executor transport."""
                entry["pending_verification"] = True
                entry["phase"] = "ready"
                write_json(checkpoint, state)
                native = sorted((codex_home / "sessions").rglob("*.jsonl"))
                attempt = len(entry.get(f"verdicts_day{day}", [])) + 1
                try:
                    verdict = harness.verify(control_runtime, workspace, native, attempt, config,
                                             repository=REPOSITORY, execute=execute, guard=guard)
                finally:
                    record_workspace_exit(workspace, entry, entry["segments"][-1])
                    write_json(checkpoint, state)
                entry.setdefault("verdicts", []).append(verdict)
                entry.setdefault(f"verdicts_day{day}", []).append(verdict)
                recovery = entry.get('day1_verification_recovery')
                if day == 1 and recovery and recovery['attempt'] == attempt:
                    recovery.update(verified_at=now(), verdict_sha256=digest(
                        (control_runtime / f'verdict-{attempt}.json').read_bytes()))
                entry["reinstruction"] = verdict["reinstruct_message"]
                entry.pop("pending_verification", None)
                write_json(checkpoint, state)
                finished = (verdict["overall"] == "pass" or attempt > config["reinstruction_limit"] or
                            not verdict["reinstruct_message"])
                if not finished and not resumed_id:
                    raise harness.HarnessError("Verifier continuation needs an executor session ID")
                return finished

            if entry.get("pending_verification") and not blocked and not control_error:
                native = sorted((codex_home / "sessions").rglob("*.jsonl"))
                current_audit = audit(native, private, workspace=workspace, repository=REPOSITORY,
                                           grading_roots=audit_roots(runtime), fingerprint_cache=fingerprint_cache)
                if current_audit["status"] != "clean":
                    blocked = True
                else:
                    try:
                        day_finished = verify_executor()
                    except UsageLimitError as exc:
                        infrastructure_stop = str(exc)
                        break
                    except harness.HarnessError as exc:
                        entry["control_invalid_reason"] = exc.invalid_reason
                        control_error = entry["control_error"] = str(exc)
            remaining = (config["retry_limit"] + 1) * (config["reinstruction_limit"] + 1) - sum(not s.get("capacity_error") for s in day_segments)
            if not config["harness"]:
                remaining = config["retry_limit"] + 1 - sum(not s.get("capacity_error") for s in day_segments)
            if entry["phase"] in {"interrupted", "usage_limited", "capacity_limited"}:
                remaining = max(1, remaining)
            transport_retries = entry.get("transport_retries", 0)
            if blocked or day_finished or control_error:
                remaining = 0
            recovery = 0
            while remaining > 0:
                observed_version = version_reader()
                if observed_version != actual_version:
                    write_json(checkpoint, state)
                    write_json(out / "run-diagnostics.json", {
                        "stop_reason": "Codex version changed before executor session",
                        "recorded_version": actual_version, "observed_version": observed_version,
                        "calibration": config.get("calibration", False), "task_root": config.get("task_root", "eval/tasks"), "service_tier": config.get("service_tier")})
                    raise IncompleteRun("Codex version changed before executor session; run halted and remains resumable")
                if config["harness"]:
                    try:
                        guard.verify()
                    except harness.HarnessError as exc:
                        entry["control_invalid_reason"] = exc.invalid_reason
                        control_error = entry["control_error"] = str(exc)
                        break
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
                if "service_tier" in config:
                    argv += ["-c", "service_tier=" + json.dumps(config["service_tier"])]
                if resumed_id:
                    argv += ["-c", 'sandbox_mode="workspace-write"', resumed_id, "-"]
                    prompt = entry.get("reinstruction") or "Continue the original task from the current workspace."
                else:
                    argv += ["--sandbox", "workspace-write", "-C", str(workspace), "-"]
                    prompt = (public / ("day2.md" if day == 2 else "prompt.md")).read_bytes().decode("utf-8")
                    if config["harness"] and day == 2:
                        argv += ["-c", "developer_instructions=" + json.dumps(
                            "Approved evaluation contract (benchmark runner authorization):\n" +
                            (control_runtime / "contract.json").read_text())]
                    elif day == 1 and task_id in templates:
                        prompt += "\n\nApproved evaluation contract (benchmark runner authorization):\n" + templates[task_id].decode("utf-8")
                    elif config["harness"]:
                        prompt += "\n\nApproved evaluation contract (benchmark runner authorization):\n" + (control_runtime / "contract.json").read_text()
                segment = {"attempt": index, "started_at": now(), "events": event_path.name, "stderr": stderr_path.name, "day": day, "cli_version": observed_version}
                if recovery or (resumed_id and entry["segments"] and
                                entry["segments"][-1].get("capacity_error") and
                                entry["segments"][-1].get("day", 1) == day):
                    segment["infrastructure_recovery"] = True
                if day == 2 and not resumed_id:
                    delivered = runtime / "day2-delivered.md"
                    delivered.write_bytes(prompt.encode("utf-8"))
                    entry["day2_observation"] = {
                        "delivered_sha256": digest(prompt.encode("utf-8")),
                        "public_sha256": digest((public / "day2.md").read_bytes()),
                        "prompt_path": str(delivered), "attempt": index}
                entry["segments"].append(segment)
                entry["phase"] = "running"
                write_json(checkpoint, state)

                def started(pid: int) -> None:
                    entry["pid"] = pid
                    write_json(checkpoint, state)

                native_before = {p: digest(p.read_bytes()) for p in (codex_home / "sessions").rglob("*.jsonl")}
                tokens_before = native_token_totals(list(native_before))
                tiers_before = applied_tier_records(list((codex_home / "sessions").rglob("*.jsonl")))
                start = time.monotonic()
                try:
                    final_process = execute(
                        argv, cwd=workspace, env=executor_environment(private, codex_home), stdin=prompt,
                        stdout=event_path, stderr=stderr_path, timeout=config.get("task_timeout_seconds", {}).get(task_id, config["timeout_seconds"]), on_start=started,
                    )
                except KeyboardInterrupt:
                    interrupted = True
                    entry["phase"] = "interrupted"
                    final_process = ProcessResult(-2)
                    segment["interrupted"] = True
                segment.update({"exited_at": now(), "exit_code": final_process.returncode,
                                "timed_out": final_process.timed_out, "latency_seconds": time.monotonic() - start})
                # Pin captures before verification/grading; historical hashes are never backfilled.
                segment["evidence_sha256"] = {
                    path.name: digest(path.read_bytes())
                    for path in (event_path, stderr_path, runtime / f"final-{index}.md")
                    if guard.safe(path) and path.is_file()}
                entry.pop("pid", None)
                native_changed = [p for p in (codex_home / "sessions").rglob("*.jsonl")
                                  if native_before.get(p) != digest(p.read_bytes())]
                segment["pricing_evidence"] = capture_tier(native_changed, tiers_before,
                                                            model=config['model'], service_tier=config.get('service_tier'))
                native_usage = native_token_delta(tokens_before, native_token_totals(native_changed))
                if native_usage is not None and not interrupted and final_process.returncode != -2:
                    segment["native_usage"] = native_usage
                    segment["native_request_usage"] = native_request_usage(native_changed, native_usage,
                                                                           before=tokens_before)
                    segment["usage_evidence"] = "Native event_msg.token_count cumulative delta; output includes reasoning"
                segment["native_logs"] = [str(p) for p in native_changed]
                transport_failure = transport.classify(segment, runtime, private.redact)
                if transport_failure:
                    segment['transport_failure'] = transport_failure
                recover_partial_usage([segment], native_changed)
                settings = collect([event_path], native_changed,
                                   config["model"], config["reasoning_effort"], config.get("service_tier"))["settings_evidence"]
                segment["settings_verified"] = settings["verified"]
                if "service_tier" in config:
                    segment["service_tier_verified"] = settings["service_tier_verified"]
                try:
                    write_json(checkpoint, state)
                    current_audit = audit([runtime / saved['events'] for saved in entry['segments']] +
                                          sorted((codex_home / 'sessions').rglob('*.jsonl')),
                                          private, workspace=workspace, repository=REPOSITORY,
                                          grading_roots=audit_roots(runtime), fingerprint_cache=fingerprint_cache)
                    infrastructure_stop = usage_limit_message([event_path])
                    capacity = capacity_message([event_path])
                    if capacity and not infrastructure_stop and not interrupted and current_audit["status"] == "clean":
                        segment.update(capacity_error=True, infrastructure_recovery=True,
                                       usage_evidence="Capacity refusal before any item: zero tokens" if
                                       capacity_refusal_without_items(records(event_path)) else
                                       "Capacity refusal after work: missing usage remains unknown")
                        if capacity_refusal_without_items(records(event_path)):
                            segment["capacity_refusal_usage"] = dict.fromkeys(
                                ("input_tokens", "cached_input_tokens", "output_tokens"), 0)
                        resumed_id = session_id([event_path]) or resumed_id
                        wait = BACKOFF_SECONDS[recovery] if recovery < len(BACKOFF_SECONDS) and resumed_id else None
                        segment["recovery_wait_seconds"] = wait
                        entry["phase"] = "capacity_limited"
                        write_json(checkpoint, state)
                        if wait is None:
                            infrastructure_stop = capacity
                            break
                        sleep(wait)
                        recovery += 1
                        continue
                    remaining -= 1
                    recovery = 0
                    if infrastructure_stop:
                        break
                    if interrupted or current_audit["status"] != "clean":
                        break
                    resumed_id = session_id([event_path]) or resumed_id
                    if final_process.returncode == 0 and not final_process.timed_out:
                        transport_retries = 0
                        entry["transport_retries"] = 0
                        if not config["harness"]:
                            break
                        try:
                            native = sorted((codex_home / "sessions").rglob("*.jsonl"))
                            native_audit = audit(native, private, workspace=workspace, repository=REPOSITORY, grading_roots=audit_roots(runtime), fingerprint_cache=fingerprint_cache)
                            if native_audit["status"] != "clean":
                                break
                            if verify_executor():
                                break
                        except UsageLimitError as exc:
                            infrastructure_stop = str(exc)
                            break
                        except harness.HarnessError as exc:
                            entry["control_invalid_reason"] = exc.invalid_reason
                            control_error = str(exc)
                            entry["control_error"] = control_error
                            break
                    else:
                        if transport_retries >= config["retry_limit"]:
                            break
                        transport_retries += 1
                        entry["transport_retries"] = transport_retries
                        write_json(checkpoint, state)
                        if transport_failure:
                            wait = BACKOFF_SECONDS[min(transport_retries - 1, len(BACKOFF_SECONDS) - 1)]
                            segment['recovery_wait_seconds'] = wait
                            sleep(wait)
                finally:
                    if not interrupted:
                        record_workspace_exit(workspace, entry, segment)
                        write_json(checkpoint, state)
            if (infrastructure_stop or interrupted or blocked or control_error or not final_process or
                    current_audit is None or current_audit["status"] != "clean" or
                    transport.unresolved(transport.inspect(entry, private.redact))):
                break
            if day not in entry.setdefault("completed_days", []):
                entry["completed_days"].append(day)
                write_json(checkpoint, state)
            if two_session and day == 1 and not execution_finished:
                native = sorted((codex_home / "sessions").rglob("*.jsonl"))
                day1_audit = audit(native, private, workspace=workspace, repository=REPOSITORY,
                                        grading_roots=audit_roots(runtime), fingerprint_cache=fingerprint_cache)
                if day1_audit["status"] != "clean":
                    break
                if config["harness"]:
                    try:
                        if not entry.get(f"verdicts_day{day}"):
                            try:
                                verdict = harness.verify(control_runtime, workspace, native, 1, config,
                                                         repository=REPOSITORY, execute=execute, guard=guard)
                            finally:
                                record_workspace_exit(workspace, entry, entry["segments"][-1])
                                write_json(checkpoint, state)
                            entry.setdefault("verdicts", []).append(verdict)
                            entry.setdefault(f"verdicts_day{day}", []).append(verdict)
                            write_json(checkpoint, state)
                        harness.handoff(control_runtime, runtime, native, config,
                                        repository=REPOSITORY, execute=execute, guard=guard)
                        write_json(checkpoint, state)
                    except UsageLimitError as exc:
                        infrastructure_stop = str(exc)
                        break
                    except harness.HarnessError as exc:
                        entry["control_invalid_reason"] = exc.invalid_reason
                        control_error = entry["control_error"] = str(exc)
                        break
                entry["active_day"] = 2
                entry.pop("reinstruction", None)
                entry["transport_retries"] = 0
                entry["phase"] = "ready"
                write_json(checkpoint, state)
        if infrastructure_stop:
            entry["phase"] = "capacity_limited" if "at capacity" in infrastructure_stop.lower() else "usage_limited"
            entry["infrastructure_stop"] = infrastructure_stop
            write_json(checkpoint, state)
        elif not interrupted:
            entry["phase"] = "executed"
            write_json(checkpoint, state)
        event_paths = [runtime / segment["events"] for segment in entry["segments"]]
        native_paths = sorted((codex_home / "sessions").rglob("*.jsonl"))
        access_audit = audit(event_paths + native_paths, private, workspace=workspace, repository=REPOSITORY, grading_roots=audit_roots(runtime), fingerprint_cache=fingerprint_cache)
        write_json(task_out / "access-audit.json", json.loads(private.redact(json.dumps(access_audit))))
        telemetry = collect(event_paths, native_paths, config["model"], config["reasoning_effort"], config.get("service_tier"))
        telemetry["executor_runs"] = collect_runs(event_paths, native_paths, entry["segments"])
        # Extract only settings and token/rate-limit evidence from native transcripts.
        selected = [event for path in native_paths for event in records(path)
                    if event.get("type") == "turn_context" or
                    (event.get("type") == "event_msg" and event.get("payload", {}).get("type") in
                     {"token_count", "thread_settings_applied"})]
        (task_out / "session-evidence.jsonl").write_text(checkout_text(private.redact("".join(json.dumps(e) + "\n" for e in selected))))
        for segment, path in zip(entry["segments"], event_paths):
            publish(path, task_out / path.name, private, source_root=runtime)
            publish(runtime / segment["stderr"], task_out / segment["stderr"], private, source_root=runtime)
            final = runtime / f'final-{segment["attempt"]}.md'
            if final.exists():
                publish(final, task_out / final.name, private, source_root=runtime)
        # Only the explicit runner manifest is eligible. Never search workspace.
        for name, expected_hash in guard.hashes.items():
            evidence = runtime / name
            target = control_target(evidence, runtime, task_out)
            if (guard.safe(evidence) and evidence.is_file() and
                    digest(evidence.read_bytes()) == expected_hash and
                    target is not None):
                target.parent.mkdir(parents=True, exist_ok=True)
                publish(evidence, target, private, source_root=runtime)
        if infrastructure_stop:
            stop_reason = private.redact("STOP-E1: " + ("capacity error" if "at capacity" in infrastructure_stop.lower() else "usage limit") + "; run remains resumable. " + infrastructure_stop)
            break
        if config["harness"]:
            try:
                guard.verify()
            except harness.HarnessError as exc:
                entry["control_invalid_reason"] = exc.invalid_reason
                control_error = entry["control_error"] = str(exc)
        transport_failures = transport.inspect(entry, private.redact)
        invalid = [transport.REASON] if transport.unresolved(transport_failures) else []
        if control_error:
            specific = entry.get("control_invalid_reason")
            invalid.append("control_timeout" if specific == "control_timeout" else "control_cli_error")
            if specific and specific not in invalid:
                invalid.append(specific)
        observation = entry.get("day2_observation")
        if two_session and not valid_day2_observation(entry, public):
            invalid.append("missing_two_session_handoff_observation")
        if two_session and observation:
            write_json(task_out / "handoff-evidence.json", observation)
        if access_audit["status"] != "clean":
            invalid.append("grader_access_detected" if access_audit["status"] == "access_detected" else "incomplete_access_audit")
        if not telemetry["settings_evidence"]["verified"] or (two_session and
                any(not s.get("settings_verified") for s in entry["segments"] if not s.get("capacity_error"))):
            invalid.append("executor_settings_unverified")
        if "service_tier" in config and (not telemetry["settings_evidence"]["service_tier_verified"] or
                any(not s.get("service_tier_verified") for s in entry["segments"] if not s.get("capacity_error"))):
            invalid.append("executor_service_tier_missing_or_different")
        if interrupted:
            invalid.append("execution_interrupted")
        invalid.extend(native_version_reasons(native_paths,
            [session_id([path]) for path in event_paths], actual_version))
        grading = None
        if final_process and final_process.returncode == 0 and not final_process.timed_out and not invalid:
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
                  "invalid_reasons": invalid, "attempts": max(1, sum(not s.get("capacity_error") for s in entry["segments"])),
                  "session_id": session_id(event_paths), "segments": entry["segments"],
                  "two_session": two_session, "day2_observation": observation,
                  "grader_access_audit": access_audit, "grading": grading, "verdicts": entry.get("verdicts", []),
                  "diagnostics": {"executor_transport_failures": transport_failures}, **telemetry}
        if 'day1_verification_recovery' in entry:
            result['day1_verification_recovery'] = entry['day1_verification_recovery']
        write_json(task_out / "result.json", json.loads(private.redact(json.dumps(result))))
        # Preserve completed source only; no private grader or grading copy is published.
        if grading and grading.get("executor_already_exited") and not (task_out / "workspace").exists():
            shutil.copytree(workspace, task_out / "workspace", ignore=WORKSPACE_COPY_IGNORE)
        entry["phase"] = "interrupted" if interrupted else "finished"
        if not interrupted:
            entry["result"] = json.loads(private.redact(json.dumps(result)))
        write_json(checkpoint, state)
        if interrupted or (final_process and (final_process.returncode != 0 and not final_process.timed_out)
                           and not transport.unresolved(transport_failures)):
            stop_reason = "STOP-E1: executor interrupted or could not complete non-interactively; inspect retained logs before another live call."
            break
    tasks = [json.loads((out / task / "result.json").read_text()) for task in order if (out / task / "result.json").exists()]
    attempted = sum(bool(entry.get("segments")) for entry in state["tasks"].values())
    configured = len(config["tasks"])
    write_json(out / "run-diagnostics.json", {
        "calibration": config.get("calibration", False), "task_root": config.get("task_root", "eval/tasks"), "service_tier": config.get("service_tier"),
        "stop_reason": stop_reason, "attempted_tasks": attempted, "configured_tasks": configured,
        "executor_transport_failures": transport.summary(state["tasks"]),
        "infrastructure_recoveries": [
            {"task_id": task_id, **segment} for task_id, entry in state["tasks"].items()
            for segment in entry["segments"] if segment.get("infrastructure_recovery")
        ] + [{"task_id": task_id, **json.loads((Path(entry["runtime"]) / name).read_text())}
             for task_id, entry in state["tasks"].items()
             for name in entry.get("control_files", {}) if name.endswith("/recovery.json")],
        "executor_runs": [{"task_id": t["task_id"], **segment}
                          for t in tasks for segment in t.get("executor_runs", [])],
    })
    if stop_reason or {t["task_id"] for t in tasks} != set(config["tasks"]):
        reason = stop_reason or "Incomplete configured task results"
        raise IncompleteRun(f"{reason} Halted after {attempted} of {configured} tasks; "
                            f"attempted={attempted}, configured={configured}")
    pricing = json.loads((REPOSITORY / "eval/prices.yaml").read_text())
    try:
        shared_tasks = [retained_tasks[t["task_id"]] if t["task_id"] in retained_tasks else
                       build_task(t, state["tasks"][t["task_id"]], out / t["task_id"], config, pricing,
                                  json.loads((task_directory(config) / t["task_id"] / "meta.json").read_text())) for t in tasks]
        report = build(config, state, shared_tasks, actual_version, REPOSITORY)
    except ValueError as exc:
        raise ReportError("Runtime report accounting or validation failed") from exc
    destination = out / "report.json"
    # Redaction is mandatory even if future report fields unexpectedly contain a private marker.
    text = json.dumps(report, indent=2) + "\n"
    for private in private_by_task.values():
        text = private.redact(text)
    destination.write_text(checkout_text(text))
    return destination
