"""Deterministic human review of public verdicts and report grading outcomes."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random
import re
from typing import Any

from jsonschema import ValidationError

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
        validate(value, schema)
    except ValidationError as exc:
        raise SampleInputError(f"invalid {label}: {exc.message}") from exc
    return value


def _verdict_path(root: Path, supplied: str) -> Path:
    path = Path(supplied)
    try:
        resolved = (path if path.is_absolute() else root / path).resolve()
    except (OSError, ValueError) as exc:
        raise SampleInputError(f"cannot resolve verdict path: {supplied}") from exc
    if not resolved.is_relative_to(root):
        raise SampleInputError("verdict artifact must stay inside the report directory")
    return resolved


def sample_report(reports: Path, n: int = 20) -> dict[str, Any]:
    """Validate every listed verdict, then take seeded rounds across task types.

    Only report.json and hash-pinned verdict artifacts are opened. In particular,
    grading copies, grader sources, grading logs and executor logs are not inputs.
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
        for artifact in sorted(task["artifacts"], key=lambda item: item["path"]):
            if not VERDICT_NAME.fullmatch(Path(artifact["path"]).name):
                continue
            path = _verdict_path(root, artifact["path"])
            if path in paths:
                raise SampleInputError("verdict artifact listed more than once")
            paths.add(path)
            data = _read(path)
            if hashlib.sha256(data).hexdigest() != artifact["sha256"]:
                raise SampleInputError(f"verdict SHA-256 mismatch: {path}")
            verdict = _load(data, "verdict.schema.json", str(path))
            groups[task["task_type"]].append({
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
