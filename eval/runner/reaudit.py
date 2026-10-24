"""Read-only re-audit of a finished run's retained external runtime logs."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
from typing import Any

from eval.runner import core
from eval.runner.audit import FingerprintCache, PrivateGraders, audit_retained_logs, interrupted_logs, digest
from eval.runner.workspace_verification import verify as verify_workspace
from eval.runner.day1_recovery import pending_verification


class InputParser(argparse.ArgumentParser):
    """Keep argument errors from echoing private paths."""

    def error(self, message: str) -> None:
        raise ValueError("Invalid re-audit arguments")


def reaudit(private_root: Path, out: Path) -> list[dict[str, Any]]:
    """Return labels only; never rewrite a checkpoint, report or audit artifact."""
    state = json.loads((out / "checkpoint.json").read_text())
    report = json.loads((out / "report.json").read_text())
    from eval.runner.schema_compat import validate_schema
    from jsonschema import ValidationError
    try:
        validate_schema(report, core.REPOSITORY)
    except ValidationError as exc:
        raise ValueError("Report schema validation failed") from exc
    tasks = state.get("tasks")
    if (state.get("report_schema") not in {"evaluation-report-v1", "evaluation-report-v2"} or not isinstance(tasks, dict) or
            not tasks or any(not re.fullmatch(r"[a-z0-9][a-z0-9-]*", task) for task in tasks) or
            {task["task_id"] for task in report["tasks"]} != set(tasks)):
        raise ValueError("A complete version-1 run is required")
    if any(entry.get("phase") != "finished" or entry.get("pid") for entry in tasks.values()):
        raise ValueError("Every executor must have finished")
    rows = []
    published_tasks = {task['task_id']: task for task in report['tasks']}
    fingerprint_cache = FingerprintCache()
    for task, entry in sorted(tasks.items()):
        errors: set[str] = set()
        labels: list[str] = []
        try:
            private = PrivateGraders.load(private_root, task, core.REPOSITORY,
                                          task_root=state.get('config', {}).get('task_root'))
            runtime = Path(entry["runtime"])
            workspace = runtime / "workspace"
            segments = entry["segments"]
            if (not runtime.is_absolute() or not segments or any(
                    Path(segment["events"]).name != segment["events"] for segment in segments)):
                raise ValueError("Invalid retained runtime manifest")
            paths = [runtime / segment["events"] for segment in segments]
            paths.extend(sorted((runtime / "codex-home/sessions").rglob("*.jsonl")))
            audit = audit_retained_logs(paths, private, interrupted_paths=interrupted_logs(runtime, entry["segments"]), retained_context=entry.get("retained_audit_context"), workspace=workspace, repository=core.REPOSITORY,
                               grading_roots=core.audit_roots(runtime), fingerprint_cache=fingerprint_cache)
            errors = {error.split(":", 1)[0] for error in audit["errors"]}
            labels = sorted({match["marker"] for match in audit["matches"]})
            # Detect lost/changed retained evidence as well as parser errors.
            previous = entry["result"]["grader_access_audit"]
            expected = Counter((log["name"], log["sha256"], log["bytes"]) for log in previous["logs"])
            observed = Counter((log["name"], log["sha256"], log["bytes"]) for log in audit["logs"])
            if not expected or observed != expected:
                errors.add("retained_log_manifest_mismatch")
            if (previous["root_fingerprint"] != digest(str(private.root).encode()) or
                    previous["grader_fingerprints"] != [digest(path.read_bytes()) for path in private.files]):
                errors.add("private_grader_manifest_mismatch")
            if not workspace.is_dir():
                errors.add("missing_retained_workspace")
            elif ("workspace_exit_sha256" in entry and
                  not (pending_verification(entry, state.get('config', {})) and
                       'workspace_exit_sha256' not in segments[-1]) and
                  verify_workspace(workspace, entry, published_tasks[task],
                                   published_workspace=out / task / 'workspace') is None):
                errors.add("workspace_exit_hash_mismatch")
        except Exception:
            # Exceptions can contain grader paths or source. Do not serialize them.
            errors.add("reaudit_input_error")
        status = "access_detected" if labels else "inconclusive" if errors else "clean"
        rows.append({"task_id": task, "status": status, "error_kinds": sorted(errors), "match_labels": labels})
    return rows


def main() -> int:
    """Print one sanitized JSON row per task, with no path or source contents."""
    parser = InputParser(description=__doc__)
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="Existing finished run directory (read only)")
    try:
        args = parser.parse_args()
        rows = reaudit(args.private_root, args.out)
    except Exception:
        print("Re-audit input error: finished run evidence unavailable", file=sys.stderr)
        return 1
    for row in rows:
        print(json.dumps(row, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
