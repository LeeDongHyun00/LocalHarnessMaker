"""Paired finished-report comparison: python -m eval.runner.compare LEFT RIGHT --out DIR."""

import json
from pathlib import Path
import sys
from typing import Any, Callable

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from eval.__main__ import InputParser
from eval.metrics import METHOD, metric, total
from eval.runner.publication import checkout_text
from eval.runner.audit import digest
from eval.runner.compare_versions import require_same_codex_version

Task = dict[str, Any]
Pair = dict[str, Task]


def cost_per_pass(tasks: list[Task]) -> float | None:
    """Preserve unknown costs and zero passing-task denominators."""
    passes = sum(t["outcome"] == "pass" for t in tasks)
    cost = total([t["costs"]["total_usd"] for t in tasks])
    return cost / passes if passes and cost is not None else None


def summarize(pairs: list[Pair], seed: int) -> dict[str, Any]:
    """Resample matched task clusters together, retaining undefined replicates."""
    functions: dict[str, Callable[[list[Task]], float | None]] = {
        "pass_rate": lambda s: sum(t["outcome"] == "pass" for t in s) / len(s) if s else None,
        "cost_per_pass": cost_per_pass,
        "avg_attempts": lambda s: sum(t["attempts"] for t in s) / len(s) if s else None,
    }
    result: dict[str, Any] = {}
    for side in ("left", "right"):
        tasks = [p[side] for p in pairs]
        result[side] = {name: metric(tasks, "matched_valid_task", len(tasks), fn, seed=seed)
                        for name, fn in functions.items()}
        eligible = [t for t in tasks if t["two_session"]]
        result[side]["handoff_success"] = metric(eligible, "matched_valid_two_session_task", len(eligible),
            lambda s: sum(t["handoff"]["day2_pass"] and not t["handoff"]["user_restated_day1_context"]
                          for t in s) / len(s), seed=seed)

    def difference(sample: list[Pair], name: str, ratio: bool = False) -> float | None:
        left, right = (functions[name]([p[side] for p in sample]) for side in ("left", "right"))
        if left is None or right is None or (ratio and right == 0):
            return None
        return left / right if ratio else left - right

    result["paired"] = {
        "pass_rate_difference": metric(pairs, "matched_valid_task", len(pairs),
            lambda s: difference(s, "pass_rate"), seed=seed),
        "cost_per_pass_difference": metric(pairs, "matched_valid_task", len(pairs),
            lambda s: difference(s, "cost_per_pass"), seed=seed),
        "cost_per_pass_ratio": metric(pairs, "matched_valid_task", len(pairs),
            lambda s: difference(s, "cost_per_pass", True), seed=seed),
    }
    return result


def compare(left: Task, right: Task) -> dict[str, Any]:
    """Match intersections; refuse incompatible populations or executor provenance."""
    require_same_codex_version([left, right])
    for field in ("task_set_sha256", "seed", "executor_model", "cost_basis", "pricing"):
        if left["metadata"][field] != right["metadata"][field]:
            raise ValueError(f"Cannot compare different {field}")
    indexed = []
    for report in (left, right):
        tasks = {t["task_id"]: t for t in report["tasks"]}
        if len(tasks) != len(report["tasks"]) or len(tasks) != report["accounting"]["attempted_tasks"]:
            raise ValueError("Duplicate tasks or incomplete accounting")
        indexed.append(tasks)
    ids = sorted(indexed[0].keys() & indexed[1].keys())
    if not ids:
        raise ValueError("No matched tasks")
    pairs = []
    invalid = []
    for task in ids:
        a, b = indexed[0][task], indexed[1][task]
        if (a["task_type"], a["two_session"]) != (b["task_type"], b["two_session"]):
            raise ValueError("Matched task metadata differs")
        if a["outcome"] == "invalid" or b["outcome"] == "invalid":
            invalid.append(task)
        else:
            pairs.append({"left": a, "right": b})
    seed = left["metadata"]["seed"]
    return {"status": "diagnostic" if invalid else "valid", "invalid_matched_tasks": invalid,
            "matched_task_ids": ids, "excluded_left": sorted(indexed[0].keys() - set(ids)),
            "excluded_right": sorted(indexed[1].keys() - set(ids)),
            "direction": "left minus right; ratio left / right",
            "cost_scope": "Tasks valid in both reports only; diagnostic if any matched task is invalid.",
            "confidence": {"seed": seed, "resamples": 10000, "level": .95, "method": METHOD},
            "overall": summarize(pairs, seed),
            "by_task_type": {kind: summarize([p for p in pairs if p["left"]["task_type"] == kind], seed)
                             for kind in sorted({indexed[0][t]["task_type"] for t in ids})}}


def markdown(result: Task) -> str:
    """Render side metrics and paired intervals in a compact review table."""
    def fmt(item: Task) -> str:
        value = item["value"]
        if value is None:
            return f"undefined (n={item['sample_size']})"
        ci = item["ci95"]
        return f"{value:.6g} [{ci['lower']:.6g}, {ci['upper']:.6g}] (n={item['sample_size']})"
    lines = [f"Comparison status: {result['status']}. Direction: {result['direction']}.",
             result["cost_scope"], "", "| Scope | Metric | Left | Right | Paired estimate [95% CI] |",
             "| --- | --- | --- | --- | --- |"]
    for scope, data in [("overall", result["overall"]), *result["by_task_type"].items()]:
        for name in ("pass_rate", "cost_per_pass", "avg_attempts", "handoff_success"):
            paired = data["paired"].get(name + "_difference")
            lines.append(f"| {scope} | {name} | {fmt(data['left'][name])} | {fmt(data['right'][name])} | {fmt(paired) if paired else '—'} |")
        lines.append(f"| {scope} | cost_per_pass ratio | — | — | {fmt(data['paired']['cost_per_pass_ratio'])} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    """Write comparison.json and comparison.md; print exactly the supplied directory."""
    parser = InputParser()
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    try:
        args = parser.parse_args()
        paths = [args.left, args.right]
        if any(args.out.resolve() == p.resolve().parent for p in paths):
            raise ValueError("Comparison destination must differ from source report directories")
        contents = [p.read_bytes() for p in paths]
        reports = [json.loads(b) for b in contents]
        schema = json.loads((Path(__file__).resolve().parents[2] / "schemas/evaluation-report.schema.json").read_text())
        for report in reports:
            Draft202012Validator(schema, format_checker=FormatChecker()).validate(report)
        result = compare(*reports)
        result["sources"] = [{"path": checkout_text(str(p)), "sha256": digest(b)} for p, b in zip(paths, contents)]
    except (OSError, ValueError, KeyError, TypeError, ValidationError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 1
    try:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")
        (args.out / "comparison.md").write_text(markdown(result))
    except Exception as exc:
        print(f"Internal error: {type(exc).__name__}", file=sys.stderr)
        return 2
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
