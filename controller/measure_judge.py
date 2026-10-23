"""Approval-gated host calibration: one codex_cli generation per authored case."""

import argparse
import hashlib
import json
import math
import shutil
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
from typing import Any

from controller.__main__ import write_json
from controller.analyze import calculate_cost
from controller.backends.base import Backend, Message, Usage, configured_prices
from controller.backends.codex_cli import CodexCLIBackend
from controller.errors import BackendError, InputError
from controller.generation import validate_input
from controller.judge import artifact_snapshot, generate_judgment
from controller.settings import PACKAGE_DIR, load_object

CASES = PACKAGE_DIR.parent / "tests/controller/fixtures/judge-calibration"
STATUSES = ("pass", "fail", "unverifiable")


def load_cases(source: Path = CASES) -> list[dict[str, Any]]:
    """Validate the entire fixed synthetic population before any paid call."""
    cases = []
    for path in sorted(source.glob("*/case.json")):
        case = load_object(path)
        if (set(case) != {"id", "criterion", "expected_status"}
                or case["id"] != path.parent.name or case["expected_status"] not in STATUSES):
            raise InputError(f"Invalid calibration case: {path}")
        validate_input(case["criterion"], "judgment-input.schema.json")
        workspace = path.parent / "workspace"
        snapshot = artifact_snapshot(workspace)
        # Hash the whole authored workspace, including omitted files, for parity.
        digest = hashlib.sha256(path.read_bytes())
        for item in sorted(workspace.rglob("*")):
            if item.is_symlink():
                raise InputError("Calibration workspace must not contain symlinks")
            if item.is_file():
                digest.update(json.dumps(str(item.relative_to(workspace))).encode())
                digest.update(hashlib.sha256(item.read_bytes()).digest())
        if not snapshot["files"]:
            raise InputError("Calibration workspace has no readable evidence")
        cases.append({**case, "workspace": workspace, "sha256": digest.hexdigest()})
    if not cases or len({case["id"] for case in cases}) != len(cases):
        raise InputError("Empty or duplicate calibration population")
    return cases


class SingleCallBackend:
    """Stop generator repair attempts before a second paid generation can occur."""

    def __init__(self, backend: Backend) -> None:
        self.backend = backend
        self.model = getattr(backend, "model", None)
        self.pricing_ref = getattr(backend, "pricing_ref", None)
        self.calls = 0

    def generate(self, schema: dict[str, Any], messages: list[Message]) -> dict[str, Any]:
        if self.calls:
            raise BackendError("Calibration permits one generation only; no repair or fallback")
        self.calls += 1
        return self.backend.generate(schema, messages)

    def usage(self) -> Usage:
        return self.backend.usage()


def measure_case(
    case: dict[str, Any], prompt_version: str, factory: Callable[[], Backend],
) -> dict[str, Any]:
    """Keep errors as calibration misses and retain failed-call accounting."""
    backend = None
    judgment, error = None, None
    started = time.monotonic()
    try:
        # Authored directory names contain labels; never expose them to the model.
        with tempfile.TemporaryDirectory(prefix="controller-judge-") as temporary:
            workspace = Path(temporary) / "workspace"
            shutil.copytree(case["workspace"], workspace)
            backend = SingleCallBackend(factory())
            judgment = generate_judgment(case["criterion"], workspace, backend,
                                         prompt_version=prompt_version)
    except (BackendError, InputError, OSError) as exc:
        error = str(exc)
    elapsed = max(0.0, time.monotonic() - started)
    # A failed constructor never starts inference; a started call may be unknown.
    usage = backend.usage() if backend is not None else Usage(0, 0, 0.0, 0.0, 0)
    actual = judgment["status"] if judgment is not None else "error"
    return {
        "id": case["id"], "sha256": case["sha256"],
        "expected_status": case["expected_status"], "actual_status": actual,
        "correct": actual == case["expected_status"],
        "judgment": judgment, "error": error,
        "generations": backend.calls if backend is not None else 0,
        "wall_seconds": elapsed, "usage": asdict(usage),
        "model": backend.model if backend is not None else None,
        "pricing_ref": backend.pricing_ref if backend is not None else None,
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Rows are expected status, columns predicted status; errors remain in denominator."""
    matrix = {expected: {actual: 0 for actual in (*STATUSES, "error")} for expected in STATUSES}
    for row in rows:
        matrix[row["expected_status"]][row["actual_status"]] += 1
    costs = [row["usage"]["usd"] for row in rows]
    latency = sum(row["wall_seconds"] for row in rows)
    return {
        "cases": len(rows), "correct": sum(row["correct"] for row in rows),
        "accuracy": sum(row["correct"] for row in rows) / len(rows) if rows else None,
        "confusion_matrix": matrix, "errors": sum(row["actual_status"] == "error" for row in rows),
        "generations": sum(row["generations"] for row in rows),
        "latency_seconds": latency, "mean_latency_seconds": latency / len(rows) if rows else None,
        "usd": sum(costs) if costs and all(cost is not None for cost in costs) else None,
        "accounting_complete": bool(costs) and all(cost is not None for cost in costs),
    }


def main(argv: list[str] | None = None, *, backend_factory: Callable[[], Backend] | None = None) -> int:
    """Preview the paid batch estimate, refuse without approval, then write a report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--prompt-version", choices=("v1", "v2"), default="v2")
    parser.add_argument("--i-have-approval", action="store_true")
    parser.add_argument("--estimated-input-tokens", type=int, default=17000)
    parser.add_argument("--estimated-output-tokens", type=int, default=1000)
    args = parser.parse_args(argv)
    try:
        cases = load_cases()
        config = load_object(PACKAGE_DIR / "config.yaml")["codex_cli"]
        prices, ref = configured_prices(config)
        if prices is None or min(args.estimated_input_tokens, args.estimated_output_tokens) < 0:
            raise InputError("Estimate needs configured prices and nonnegative token allowances")
        estimate = len(cases) * calculate_cost(
            args.estimated_input_tokens, args.estimated_output_tokens, prices)
        if not math.isfinite(estimate):
            raise InputError("Non-finite estimate")
        prompt_path = PACKAGE_DIR / "prompts" / (
            "judge-v1.md" if args.prompt_version == "v1" else "judge.md")
        prompt_hash = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
        print(f"Planned calls: {len(cases)} maximum, one codex_cli generation per case, "
              f"prompt {args.prompt_version}, no retries or HTTP fallback; "
              f"estimated API-equivalent USD: {estimate:.6f} "
              f"({args.estimated_input_tokens} input/{args.estimated_output_tokens} output tokens "
              "per call; planning estimate, not a cap).", flush=True)
        if not args.i_have_approval:
            print("Refusing to start without --i-have-approval.")
            return 1
        if not args.out.parent.is_dir() or args.out.exists():
            raise InputError("--out requires an existing parent and a new summary path")
        factory = backend_factory or (lambda: CodexCLIBackend(config=config))
        rows = []
        for case in cases:
            rows.append(measure_case(case, args.prompt_version, factory))
            print(f"calibration {case['id']}: {rows[-1]['actual_status']}", file=sys.stderr, flush=True)
        write_json(args.out, {
            "backend": "codex_cli", "config": config, "prompt_version": args.prompt_version,
            "prompt_sha256": prompt_hash, "estimate_pricing_ref": ref,
            "estimated_usd": estimate, "maximum_generations": len(cases),
            "cost_basis": "api_equivalent_usd", "sample_source": str(CASES.relative_to(PACKAGE_DIR.parent)),
            "policy": "one generation per case; no retries or HTTP fallback; errors count as misses",
            "samples": rows, "totals": summarize(rows),
        })
    except (OSError, ValueError, InputError) as exc:
        print(f"measurement: {exc}", file=sys.stderr)
        return 1
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
