"""Opt-in host measurement of the production contract pipeline without HTTP."""

import argparse
import io
import json
import logging
import math
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

from controller.__main__ import main as controller_main, write_json
from controller.analyze import calculate_cost
from controller.backends.base import configured_prices
from controller.backends.routing import RoutedBackend
from controller.errors import InputError
from controller.generation import schema_validator
from controller.settings import PACKAGE_DIR, load_object

ROOT = PACKAGE_DIR.parent
CHECK_TYPES = ("command", "file_exists", "regex", "llm_judge")
MAX_GENERATIONS = 3


def measurement_backend(selected: str) -> RoutedBackend:
    """Use production routing and its shared budget, with HTTP disabled in memory."""
    if selected != "codex_cli":
        raise InputError("Measurement supports codex_cli only")
    config = load_object(PACKAGE_DIR / "config.yaml")
    config["fallback"]["enabled"] = False
    return RoutedBackend(selected, config=config)


def measure_sample(sample: dict[str, Any], directory: Path) -> dict[str, Any]:
    """Invoke controller contract with scoped log capture and no HTTP route."""
    prompt, output = directory / "prompt.json", directory / "contract.json"
    prompt.write_text(json.dumps(sample["prompt"]), encoding="utf-8")
    logs, stdout = io.StringIO(), io.StringIO()
    handler = logging.StreamHandler(logs)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root = logging.getLogger()
    previous_handlers, previous_level = root.handlers[:], root.level
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    try:
        with redirect_stderr(logs), redirect_stdout(stdout):
            code = controller_main([
                "contract", "--prompt", str(prompt), "--handoff", "none",
                "--cases", str(PACKAGE_DIR / "case_library/seed"),
                "--backend", "codex_cli", "--out", str(output),
            ], backend_factory=measurement_backend)
    finally:
        root.handlers, root.level = previous_handlers, previous_level
    calls = [json.loads(line.removeprefix("control_call "))
             for line in logs.getvalue().splitlines() if line.startswith("control_call ")]
    valid, assumptions, counts = False, None, None
    if code == 0 and output.is_file():
        value = load_object(output)
        valid = schema_validator("contract.schema.json").is_valid(value)
        if valid:
            assumptions = len(value["assumptions"])
            counts = {kind: sum(item["check"]["type"] == kind
                               for item in value["success_criteria"]) for kind in CHECK_TYPES}
    accounting = bool(calls) and all(call.get("backend") == "codex_cli" for call in calls)
    gate_fired = any(line.startswith("contract_quality_gate ")
                     for line in logs.getvalue().splitlines())
    return {
        "id": sample["id"], "ambiguous": sample["ambiguous"], "exit_code": code,
        "schema_valid": valid, "assumptions_count": assumptions, "criteria_by_type": counts,
        "quality_gate_fired": gate_fired, "generations": len(calls),
        "errors": [line for line in logs.getvalue().splitlines()
                   if line.startswith("controller:")],
        "latency_seconds": (sum(call["latency_seconds"] for call in calls)
                            if accounting else None),
        "usd": (sum(call["usd"] for call in calls)
                if accounting and all(call.get("usd") is not None for call in calls) else None),
        "control_calls": calls,
        "accounting_complete": accounting and all(call.get("usd") is not None for call in calls),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate valid contracts; missing accounting never becomes free usage."""
    counts = {kind: sum(row["criteria_by_type"][kind] for row in rows
                        if row["schema_valid"]) for kind in CHECK_TYPES}
    criteria = sum(counts.values())
    complete = all(row["accounting_complete"] for row in rows)
    return {
        "samples": len(rows), "schema_valid": sum(row["schema_valid"] for row in rows),
        "quality_gate_firings": sum(row["quality_gate_fired"] for row in rows),
        "generations": sum(row["generations"] for row in rows),
        "schema_pass_rate": sum(row["schema_valid"] for row in rows) / len(rows),
        "assumptions_count": sum(row["assumptions_count"] for row in rows if row["schema_valid"]),
        "criteria_by_type": counts, "criteria_count": criteria,
        "llm_judge_share": counts["llm_judge"] / criteria if criteria else None,
        "llm_judge_share_basis": "schema-valid contracts only",
        "usd": sum(row["usd"] for row in rows) if complete else None,
        "latency_seconds": (sum(row["latency_seconds"] for row in rows)
                            if all(row["latency_seconds"] is not None for row in rows) else None),
        "accounting_complete": complete,
    }


def main(argv: list[str] | None = None) -> int:
    """Print an estimate before the approval gate, then write one JSON summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--i-have-approval", action="store_true")
    parser.add_argument("--estimated-input-tokens", type=int, default=17000)
    parser.add_argument("--estimated-output-tokens", type=int, default=1000)
    args = parser.parse_args(argv)
    try:
        # Use only our authored 30-sample set; never discover evaluation tasks.
        source = ROOT / "tests/controller/fixtures/requests-v1.json"
        samples = json.loads(source.read_text(encoding="utf-8"))
        if (not isinstance(samples, list) or not samples
                or any(not isinstance(s, dict) or not isinstance(s.get("id"), str)
                       or not isinstance(s.get("prompt"), str) or not s["prompt"].strip()
                       or type(s.get("ambiguous")) is not bool for s in samples)
                or len({s["id"] for s in samples}) != len(samples)):
            raise InputError("Invalid authored sample set")
        config = load_object(PACKAGE_DIR / "config.yaml")["codex_cli"]
        prices, ref = configured_prices(config)
        if prices is None:
            raise InputError("No price snapshot for estimate")
        max_calls = len(samples) * MAX_GENERATIONS
        estimate = max_calls * calculate_cost(
            args.estimated_input_tokens, args.estimated_output_tokens, prices)
        if not math.isfinite(estimate):
            raise InputError("Non-finite estimate")
        print(f"Planned calls: {max_calls} maximum, up to {MAX_GENERATIONS} codex_cli "
              "generations per sample, no HTTP fallback; "
              f"estimated API-equivalent USD: {estimate:.6f} "
              f"({args.estimated_input_tokens} input/{args.estimated_output_tokens} output "
              "tokens per generation, no cache discount; planning estimate, not a cap).", flush=True)
        if not args.i_have_approval:
            print("Refusing to start without --i-have-approval.")
            return 1
        if not args.out.parent.is_dir() or args.out.exists():
            raise InputError("--out requires an existing parent and a new summary path")
        rows = []
        for sample in samples:
            with tempfile.TemporaryDirectory(prefix="controller-measure-") as temporary:
                rows.append(measure_sample(sample, Path(temporary)))
        write_json(args.out, {
            "backend": "codex_cli", "model": config["model"],
            "sample_source": str(source.relative_to(ROOT)),
            "estimated_usd": estimate, "estimate_pricing_ref": ref,
            "maximum_generations": max_calls,
            "cheap_api": {"status": "not measured", "reason": "HTTP fallback disabled for measurement"},
            "local": {"status": "not measured", "reason": "Dropped by decision 0007"},
            "samples": rows, "totals": summarize(rows),
        })
    except (OSError, ValueError, InputError) as exc:
        print(f"measurement: {exc}")
        return 1
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
