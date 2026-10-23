"""Deterministic human review of public verdicts and report grading outcomes."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random
import re
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from verifier.schema import validate


SEED = 42
OUTPUT_NAME = "verifier-sample.json"
VERDICT_NAME = re.compile(r"(?:.*-)?verdict(?:-[0-9]+)?\.json\Z")


class SampleInputError(ValueError):
    """A report or its listed public verdict evidence cannot be used."""


def _read(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise SampleInputError(f"cannot read {path}: {exc}") from exc


def _load(data: bytes, schema: str, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data)
    except ValueError as exc:
        raise SampleInputError(f"invalid JSON in {label}: {exc}") from exc
    try:
        if (schema == "evaluation-report.schema.json" and isinstance(value, dict)
                and isinstance(value.get("metrics"), dict)
                and "task_false_done_rate" not in value["metrics"]):
            # Decision 0009 preserves v1 reports without rewriting their metrics.
            record = Path(__file__).resolve().parents[1] / "docs/decisions/0003-evaluation-report-schema-proposal.md"
            original = record.read_text(encoding="utf-8").split("```json\n", 1)[1].split("```", 1)[0]
            Draft202012Validator(json.loads(original), format_checker=FormatChecker()).validate(value)
        else:
            validate(value, schema)
    except ValidationError as exc:
        raise SampleInputError(f"invalid {label}: {exc.message}") from exc
    return value


def _artifact_path(root: Path, supplied: str) -> Path:
    path = Path(supplied)
    prefix = Path("eval/reports") / root.name
    if not path.is_absolute() and path.is_relative_to(prefix):
        path = path.relative_to(prefix)
    try:
        resolved = (path if path.is_absolute() else root / path).resolve()
    except (OSError, ValueError) as exc:
        raise SampleInputError(f"cannot resolve artifact path: {supplied}") from exc
    if not resolved.is_relative_to(root):
        raise SampleInputError("sample artifact must stay inside the report directory")
    return resolved


def _read_artifact(root: Path, artifact: dict[str, str], paths: set[Path]) -> tuple[Path, bytes]:
    path = _artifact_path(root, artifact["path"])
    if path in paths:
        raise SampleInputError("sample artifact listed more than once")
    paths.add(path)
    data = _read(path)
    if hashlib.sha256(data).hexdigest() != artifact["sha256"]:
        raise SampleInputError(f"sample artifact SHA-256 mismatch: {path}")
    return path, data


def sample_report(reports: Path, n: int = 20) -> dict[str, Any]:
    """Validate every listed verdict, then take seeded rounds across task types.

    Only report.json and hash-pinned verdict/result artifacts are opened. Listed
    standalone verdicts take precedence over inline result verdicts per task.
    Grading copies, grader sources, grading logs and executor logs are not inputs.
    """
    if n < 1:
        raise SampleInputError("--n must be at least 1")
    root = reports.resolve()
    report_bytes = _read(root / "report.json")
    report = _load(report_bytes, "evaluation-report.schema.json", "report.json")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    task_ids: set[str] = set()
    paths: set[Path] = set()
    for task in sorted(report["tasks"], key=lambda item: item["task_id"]):
        if task["task_id"] in task_ids:
            raise SampleInputError("duplicate task_id in report.json")
        task_ids.add(task["task_id"])
        artifacts = sorted(task["artifacts"], key=lambda item: item["path"])
        standalone = [a for a in artifacts if VERDICT_NAME.fullmatch(Path(a["path"]).name)]
        sources = standalone or [a for a in artifacts if Path(a["path"]).name == "result.json"]
        for artifact in sources:
            path, data = _read_artifact(root, artifact, paths)
            if standalone:
                verdicts = [_load(data, "verdict.schema.json", str(path))]
            else:
                try:
                    result = json.loads(data)
                except ValueError as exc:
                    raise SampleInputError(f"invalid JSON in {path}: {exc}") from exc
                if (not isinstance(result, dict) or result.get("task_id") != task["task_id"]
                        or result.get("task_type") != task["task_type"]
                        or not isinstance(result.get("verdicts"), list)):
                    raise SampleInputError(f"invalid task identity or verdicts array in {path}")
                verdicts = result["verdicts"]
                for index, verdict in enumerate(verdicts):
                    try:
                        validate(verdict, "verdict.schema.json")
                    except ValidationError as exc:
                        raise SampleInputError(f"invalid {path}#/verdicts/{index}: {exc.message}") from exc
            for index, verdict in enumerate(verdicts):
                source = {} if standalone else {"verdict_index": index}
                groups[task["task_type"]].append({
                    **source,
                    "task_id": task["task_id"], "task_type": task["task_type"],
                    "verdict_path": path.relative_to(root).as_posix(),
                    "verdict_sha256": artifact["sha256"],
                    "attempt": verdict["attempt"], "overall": verdict["overall"],
                    "items": verdict["items"], "task_outcome": task["outcome"],
                    "final_grading_outcome": task["grading"]["result"] if task["grading"] else None,
                    "invalid_reasons": task["invalid_reasons"],
                })
    rng = random.Random(SEED)
    types = sorted(groups)
    rng.shuffle(types)
    for task_type in types:
        rng.shuffle(groups[task_type])
    available = sum(len(group) for group in groups.values())
    samples = []
    while len(samples) < min(n, available):
        for task_type in types:
            if groups[task_type] and len(samples) < n:
                samples.append(groups[task_type].pop())
    return {"seed": SEED, "requested": n, "available": available,
            "report_sha256": hashlib.sha256(report_bytes).hexdigest(),
            "samples": samples}
