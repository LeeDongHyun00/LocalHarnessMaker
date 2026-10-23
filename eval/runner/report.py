"""Translate retained runner evidence into the approved version-1 report."""

from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from eval.runner.publication import checkout_text, evidence_path

from eval.metrics import METHOD, compute, metric, total
from eval.runner.audit import digest
from eval.runner.control_accounting import control_calls
from eval.runner.telemetry import records, session_id
from eval.runner.limits import capacity_message, capacity_refusal_without_items


def artifact(path: Path) -> dict[str, str]:
    """Pin an existing artifact, including external unredacted event evidence."""
    return {"path": checkout_text(str(path)), "sha256": digest(path.read_bytes())}


def usage(events: Path, latency: float, model: str, pricing: dict[str, Any], *, tier: str = "standard", native_counts: dict[str, int] | None = None) -> dict[str, Any]:
    """Use complete per-segment counts; cache is a subset, output includes reasoning."""
    turns = [e.get("usage", {}) for e in records(events) if e.get("type") == "turn.completed"]
    counts = {key: sum(t[key] for t in turns) if turns and all(type(t.get(key)) is int and t[key] >= 0 for t in turns) else None
              for key in ("input_tokens", "cached_input_tokens", "output_tokens")}
    if native_counts is not None:
        counts = native_counts
    if capacity_refusal_without_items(records(events)):
        counts = dict.fromkeys(counts, 0)
    i, c, o = (counts[k] for k in counts)
    if i is not None and c is not None and c > i:
        raise ValueError("Cached tokens exceed input tokens")
    # Standard is the baseline CLI default assumption; explicit unknown tiers
    # and long-context requests cannot inherit the short-context price.
    observed_tiers = [e.get("service_tier", e.get("usage", {}).get("service_tier", tier))
                      for e in records(events) if e.get("type") == "turn.completed"]
    covered = tier == "standard" and all(t in {"standard", "default"} for t in observed_tiers)
    covered = covered and all(t["input_tokens"] <= 272000
                              for t in turns if type(t.get("input_tokens")) is int)
    rate = next((r for r in pricing["rates"] if r["model"] == model), None) if covered else None
    usd = None
    if rate is not None and all(v is not None for v in (i, c, o)):
        usd = ((i - c) * rate["input_per_million_usd"] + c * rate["cached_input_per_million_usd"] + o * rate["output_per_million_usd"]) / 1_000_000
    return {**counts, "usd": usd, "latency_seconds": latency, "cost_basis": "api_equivalent_usd",
            "pricing_ref": pricing["snapshot_id"] if rate else None}


def build_task(result: dict[str, Any], entry: dict[str, Any], out: Path,
               config: dict[str, Any], pricing: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    """Preserve invalid costs and represent missing observations explicitly."""
    runtime = Path(entry["runtime"])
    segments, calls = [], []
    for segment in result["segments"]:
        path = runtime / segment["events"]
        sid = session_id([path]) or result["session_id"]
        if sid and path.is_file():
            segments.append({k: segment[k] for k in ("attempt", "started_at", "exited_at", "exit_code")}
                            | {"session_id": sid, "events": artifact(path)})
        calls.append({"call_id": f'{result["task_id"]}-exec-{segment["attempt"]}', "purpose": "executor",
                      "backend": "codex_cli", "model": config["model"],
                      "status": "timeout" if segment.get("timed_out") else "completed" if segment["exit_code"] == 0 else "failed",
                      "usage": usage(path, segment.get("latency_seconds", 0), config["model"], pricing,
                                     tier=result.get("pricing_evidence", {}).get("tier", "standard"),
                                     native_counts=segment.get("native_usage"))})
    audit = result["grader_access_audit"]
    status = audit["status"]
    reason = "Observed forbidden access." if status == "access_detected" else "; ".join(audit["errors"]) if status == "inconclusive" else None
    if any(m["tool"] in {"world_state", "token_usage_record", "thread_settings_applied"} for m in audit["matches"]):
        reason = "Private location reached executor context through native metadata."
    shared_audit = {"method": "access_audit", "status": status,
                    "private_grader_roots": ["sha256:" + audit["root_fingerprint"]],
                    "reason": reason, "matches": [
                        {"event_log": m["log"], "line": m["line"], "tool": m["tool"], "path": m["marker"],
                         "operation": m["operation"], "evidence": m["redacted_evidence"]} for m in audit["matches"]]}
    invalid = list(result["invalid_reasons"])
    if len(segments) != len(result["segments"]):
        invalid.append("missing_executor_session_id")
    handoff = None
    if meta["two_session"]:
        from eval.runner.core import valid_day2_observation, REPOSITORY
        if not valid_day2_observation(entry, REPOSITORY / "eval/tasks" / result["task_id"]):
            if "missing_two_session_handoff_observation" not in invalid:
                invalid.append("missing_two_session_handoff_observation")
        elif (out / "handoff-evidence.json").is_file():
            handoff = {"day2_pass": result["outcome"] == "pass",
                       "user_restated_day1_context": False,
                       "evidence": artifact(out / "handoff-evidence.json")}
        else:
            invalid.append("missing_two_session_handoff_observation")
    grading = result["grading"]
    if invalid:
        grading = None
    elif grading and "copied_at" in grading:
        grading = {"copy_path": grading["copy_path"], "copied_at": grading["copied_at"],
                   "grader_source_outside_repo": True, "result": grading["result"],
                   "passed_tests": grading["passed_tests"], "failed_tests": grading["failed_tests"],
                   "log": artifact(out / grading["log"])}
    else:
        grading = None
    executor_usd = total([c["usage"]["usd"] for c in calls])
    controls, control_usd = control_calls(entry, result["task_id"], pricing) if config["harness"] else ([], 0)
    calls.extend(controls)
    # The verdict exposes negative done claims, but not the complete claim denominator.
    # Until a full claim observation is available, emit no measured claims and keep
    # false_done_rate undefined rather than treating unobserved claims as zero errors.
    claims = {"claimed_items": 0, "claimed_without_evidence": 0}
    return {"task_id": result["task_id"], "task_type": result["task_type"], "two_session": meta["two_session"],
            "outcome": "invalid" if invalid else result["outcome"], "invalid_reasons": invalid,
            "attempts": result["attempts"], "executor_segments": segments, "grader_access_audit": shared_audit,
            "grading": grading, "done_claims": claims, "calls": calls,
            "costs": {"executor_usd": executor_usd, "control_usd": control_usd,
                      "total_usd": total([executor_usd, control_usd])},
            "artifacts": [artifact(p) for p in [*sorted(out.iterdir()), *sorted((out / "control-interruptions").rglob("*")),
                          *sorted((runtime / "codex-home/sessions").rglob("*.jsonl"))] if p.is_file()], "handoff": handoff}


def require_same_codex_version(reports: list[dict[str, Any]]) -> str:
    """Refuse an evaluation comparison across native Codex versions."""
    versions = {report["metadata"]["codex_version"] for report in reports}
    if len(versions) != 1:
        raise ValueError("Cannot compare reports with different codex_version values")
    return versions.pop()


def native_version_reasons(paths: list[Path], session_ids: list[str | None], version: str) -> list[str]:
    """Return task-level failures without aborting other tasks' reports."""
    expected = version.removeprefix("codex-cli ")
    sessions: set[str] = set()
    reasons: set[str] = set()
    for path in paths:
        for event in records(path):
            if event.get("type") == "session_meta":
                payload = event.get("payload", {})
                if payload.get("id"):
                    sessions.add(payload["id"])
                observed = payload.get("cli_version")
                if not observed:
                    reasons.add("missing_cli_version_evidence")
                elif observed != expected:
                    reasons.add("mismatched_cli_version_evidence")
    if any(sid and sid not in sessions for sid in session_ids):
        reasons.add("missing_cli_version_evidence")
    return sorted(reasons)


def task_version_reasons(task: dict[str, Any], version: str) -> list[str]:
    """Verify retained native hashes before interpreting per-session versions."""
    paths = []
    for item in task["artifacts"]:
        path = evidence_path(item["path"])
        if "sessions" not in path.parts or path.suffix != ".jsonl":
            continue
        if digest(path.read_bytes()) != item["sha256"]:
            raise ValueError("Native session log hash mismatch")
        paths.append(path)
    return native_version_reasons(paths, [s["session_id"] for s in task["executor_segments"]], version)


def validate_session_versions(task: dict[str, Any], version: str) -> None:
    """Missing/mismatched versions require explicit task invalidation."""
    reasons = task_version_reasons(task, version)
    if reasons and (task["outcome"] != "invalid" or not set(reasons) <= set(task["invalid_reasons"])):
        raise ValueError("Native session cli_version evidence requires task invalidation: " + "; ".join(reasons))


def validate(report: dict[str, Any], repository: Path) -> None:
    """Check schema plus runtime arithmetic, IDs, chronology and log hashes."""
    Draft202012Validator(json.loads((repository / "schemas/evaluation-report.schema.json").read_text()),
                        format_checker=FormatChecker()).validate(report)
    tasks = report["tasks"]
    if len({t["task_id"] for t in tasks}) != len(tasks):
        raise ValueError("Duplicate task identifiers")
    calls = [c for t in tasks for c in t["calls"]]
    if len({c["call_id"] for c in calls}) != len(calls):
        raise ValueError("Duplicate call identifiers")
    for task in tasks:
        validate_session_versions(task, report["metadata"]["codex_version"])
        if task["attempts"] != max(1, sum(not capacity_message([evidence_path(s["events"]["path"])]) for s in task["executor_segments"])) and task["outcome"] != "invalid":
            raise ValueError("Attempt/segment count mismatch")
        previous = None
        for index, seg in enumerate(task["executor_segments"], 1):
            start, end = (datetime.fromisoformat(seg[k]) for k in ("started_at", "exited_at"))
            if end < start or previous is not None and start < previous or seg["attempt"] != index:
                raise ValueError("Executor segment ordering mismatch")
            previous = end
            if digest(evidence_path(seg["events"]["path"]).read_bytes()) != seg["events"]["sha256"]:
                raise ValueError("Executor log hash mismatch")
        if task["grading"] and previous is not None and datetime.fromisoformat(task["grading"]["copied_at"]) <= previous:
            raise ValueError("Grading must follow executor exit")
        if task["handoff"]:
            evidence = task["handoff"]["evidence"]
            observation = json.loads(evidence_path(evidence["path"]).read_text())
            if (digest(evidence_path(evidence["path"]).read_bytes()) != evidence["sha256"] or
                    observation["delivered_sha256"] != observation["public_sha256"] or
                    digest(evidence_path(observation["prompt_path"]).read_bytes()) != observation["delivered_sha256"] or
                    len({s["session_id"] for s in task["executor_segments"]}) < 2 or
                    task["handoff"]["user_restated_day1_context"] or
                    task["handoff"]["day2_pass"] != (task["outcome"] == "pass")):
                raise ValueError("Invalid day-2 prompt observation")
        if task["done_claims"]["claimed_without_evidence"] > task["done_claims"]["claimed_items"]:
            raise ValueError("Claim counts mismatch")
        for call in task["calls"]:
            u = call["usage"]
            if u["cached_input_tokens"] is not None and u["input_tokens"] is not None and u["cached_input_tokens"] > u["input_tokens"]:
                raise ValueError("Cached tokens exceed input tokens")
        executor = total([c["usage"]["usd"] for c in task["calls"] if c["purpose"] == "executor"])
        control = total([c["usage"]["usd"] for c in task["calls"] if c["purpose"] != "executor"])
        if task["costs"]["control_usd"] is not None and task["costs"]["control_usd"] != control:
            raise ValueError("Control cost mismatch")
        if task["costs"]["executor_usd"] != executor or task["costs"]["total_usd"] != total([executor, task["costs"]["control_usd"]]):
            raise ValueError("Task cost mismatch")
    expected = {"attempted_tasks": len(tasks), "valid_tasks": sum(t["outcome"] != "invalid" for t in tasks),
                "invalid_tasks": sum(t["outcome"] == "invalid" for t in tasks),
                "total_cost_usd": total([t["costs"]["total_usd"] for t in tasks])}
    if report["accounting"] != expected:
        raise ValueError("Accounting mismatch")
    sizes = {"pass_rate": expected["valid_tasks"], "avg_attempts": expected["valid_tasks"],
             "cost_per_pass": len(tasks), "false_done_rate": sum(t["done_claims"]["claimed_items"] for t in tasks if t["outcome"] != "invalid"),
             "handoff_success": sum(t["two_session"] and t["outcome"] != "invalid" for t in tasks)}
    if any(report["metrics"][key]["sample_size"] != size for key, size in sizes.items()):
        raise ValueError("Metric sample count mismatch")
    for m in report["metrics"].values():
        if m["value"] is not None and m["ci95"]["lower"] > m["ci95"]["upper"]:
            raise ValueError("Reversed confidence bounds")


def current_commit(repository: Path) -> str:
    """Read local checkout provenance without launching an executor."""
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=repository, capture_output=True,
                          text=True, check=True, timeout=10).stdout.strip()


def build(config: dict[str, Any], state: dict[str, Any], tasks: list[dict[str, Any]],
          version: str, repository: Path) -> dict[str, Any]:
    """Build a report using the versioned offline pricing provenance."""
    pricing = json.loads((repository / "eval/prices.yaml").read_text())
    commit = current_commit(repository)
    recorded_commit = state.get("git_commit", commit)
    recorded_snapshot = state.get("pricing_snapshot_id", pricing["snapshot_id"])
    if recorded_commit != commit:
        print(f"Warning: run git_commit {recorded_commit} differs from build HEAD {commit}", file=sys.stderr)
    if recorded_snapshot != pricing["snapshot_id"]:
        print(f'Warning: run pricing snapshot {recorded_snapshot} differs from build snapshot {pricing["snapshot_id"]}', file=sys.stderr)
    models = {c["model"] for t in tasks for c in t["calls"] if c["purpose"] != "executor"}
    control_model = next(iter(models)) if len(models) == 1 and "unknown" not in models else None
    if config["harness"] and control_model is None:
        print(f"Warning: control_model is null; observed control models: {sorted(models)}", file=sys.stderr)
    for task in tasks:
        reasons = task_version_reasons(task, version)
        if reasons:
            task["invalid_reasons"] = list(dict.fromkeys([*task["invalid_reasons"], *reasons]))
            task["outcome"] = "invalid"
            task["grading"] = None
            if task["handoff"]:
                task["handoff"]["day2_pass"] = False
    invalid = [f'{t["task_id"]}: {reason}' for t in tasks for reason in t["invalid_reasons"]]
    report = {"metadata": {"run_id": state["run_id"], "created_at": state["created_at"],
        "config_name": config["name"], "config_sha256": state["config_sha256"],
        "task_set_sha256": state["task_set_sha256"], "git_commit": recorded_commit, "codex_version": version,
        "executor_model": config["model"], "reasoning_effort": config["reasoning_effort"],
        "control_backend": config["control_backend"], "control_model": control_model,
        "seed": config["seed"], "reinstruction_limit": config["reinstruction_limit"],
        "cost_basis": "api_equivalent_usd", "pricing": pricing,
        "confidence": {"level": .95, "method": METHOD, "resamples": 10000, "seed": config["seed"]},
        "parity_comparator": None}, "tasks": tasks, "metrics": compute(tasks, seed=config["seed"]),
        "accounting": {"attempted_tasks": len(tasks), "valid_tasks": len(tasks) - sum(t["outcome"] == "invalid" for t in tasks),
                       "invalid_tasks": sum(t["outcome"] == "invalid" for t in tasks),
                       "total_cost_usd": total([t["costs"]["total_usd"] for t in tasks])},
        "validity": {"status": "invalid" if invalid else "valid", "reasons": invalid}}
    report["metrics"]["false_done_rate"] = metric([], "claimed_criterion", 0, lambda _: None,
        seed=config["seed"], reason="Complete done-claim denominator is not yet observed; verdicts retain negative evidence.")
    validate(report, repository)
    return report
