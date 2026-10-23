"""Price every retained control generation using the evaluation price snapshot."""

import json
from pathlib import Path
import re
from typing import Any

from eval.metrics import total
from eval.runner.pricing import select
from eval.runner.audit import digest
from eval.runner.limits import capacity_refusal_without_items
from eval.runner.publication import safe_source
from eval.runner.telemetry import _pricing_tier


def control_calls(entry: dict[str, Any], task_id: str,
                  pricing: dict[str, Any], *, provenance: list[dict[str, Any]] | None = None) -> tuple[list[dict[str, Any]], float | None]:
    """Read only hash-pinned runner evidence, including archived interruptions."""
    runtime = Path(entry["runtime"])
    pinned = entry.get("control_files", {})
    calls: list[dict[str, Any]] = []
    complete = True
    streams = [name for name in pinned if re.fullmatch(
        r"(?:contract|handoff|verdict-[0-9]+)\.stderr", Path(name).name)]

    def read(name: str) -> str | None:
        path = runtime / name
        if (Path(name).is_absolute() or not path.is_relative_to(runtime) or ".." in Path(name).parts or
                not path.is_file() or not safe_source(path, runtime) or
                digest(path.read_bytes()) != pinned.get(name)):
            return None
        return path.read_text(errors="replace")

    # A launched operation without retained stderr is incomplete too.
    manifests = [name for name in pinned if name.endswith(".control.json") and
                 Path(name).name != "handoff-validation.control.json"]
    if any(str(Path(name).with_suffix("").with_suffix(".stderr")) not in streams for name in manifests):
        complete = False
    for name in sorted(streams):
        purpose = "judge" if Path(name).name.startswith("verdict-") else Path(name).stem
        manifest_name = str(Path(name).with_suffix(".control.json"))
        manifest_text = read(manifest_name)
        try:
            process = json.loads(manifest_text) if manifest_text else {}
        except ValueError:
            process = {}
        text = read(name)
        if text is None:
            complete = False
            continue
        successful = False
        delegations: list[dict[str, Any]] = []
        count_before = len(calls)
        pending_events: dict[str, Any] | None = None
        lines = text.split("\n")
        # Each CLI transport emits its events immediately before its control_call.
        # If interrupted before that accounting line, retain the capacity call too.
        expanded: list[str] = []
        pending_line: str | None = None
        for line in lines + [""]:
            if ("control_cli_events " in line or line == "") and pending_line:
                envelope = json.loads(pending_line.split("control_cli_events ", 1)[1])
                try:
                    events = [json.loads(row) for row in envelope.get("events", "").removesuffix("\n").split("\n")]
                except (ValueError, AttributeError):
                    events = []
                if any(e.get("type") in {"error", "turn.failed"} and "at capacity" in str(e).lower()
                       for e in events if isinstance(e, dict)):
                    expanded.append("control_call " + json.dumps({"backend": "codex_cli",
                        "model": envelope.get("model"), "status": "error",
                        "latency_seconds": process.get("latency_seconds")}))
                pending_line = None
            expanded.append(line)
            if "control_cli_events " in line:
                try:
                    envelope = json.loads(line.split("control_cli_events ", 1)[1])
                    if isinstance(envelope, dict) and isinstance(envelope.get("events"), str):
                        pending_line = line
                except ValueError:
                    pass
            if line.startswith("control_call "):
                pending_line = None
        for line in expanded:
            if "control_cli_events " in line:
                try:
                    pending_events = json.loads(line.split("control_cli_events ", 1)[1])
                except ValueError:
                    pending_events = None
                continue
            marker = next((m for m in ("control_call ", "judge_delegation ") if line.startswith(m)), None)
            if marker is None:
                continue
            try:
                value = json.loads(line.split(marker, 1)[1])
                if not isinstance(value, dict):
                    raise ValueError("Expected object")
            except ValueError:
                complete = False
                continue
            if marker == "judge_delegation ":
                delegations.append(value)
                if (value.get("accounting_complete") is not True or
                        type(value.get("forwarded_control_calls")) is not int or
                        value["forwarded_control_calls"] < 0):
                    complete = False
                    value["forwarded_control_calls"] = 0
                continue
            model = value.get("model")
            if not isinstance(model, str) or not model:
                model = "unknown"
            backend = value.get("backend")
            if backend not in {"codex_cli", "cheap_api", "local"}:
                complete = False
                continue
            counts = {k: value.get(k) if type(value.get(k)) is int and value[k] >= 0 else None
                      for k in ("input_tokens", "cached_input_tokens", "output_tokens")}
            if backend == "codex_cli" and isinstance(pending_events, dict):
                try:
                    events = [json.loads(row) for row in pending_events.get("events", "").removesuffix("\n").split("\n")]
                except (ValueError, AttributeError):
                    events = []
                if capacity_refusal_without_items([e for e in events if isinstance(e, dict)]):
                    counts = dict.fromkeys(counts, 0)
            pending_events = None
            i, c, o = counts.values()
            if i is not None and c is not None and c > i:
                counts["cached_input_tokens"] = c = None
            observed_tier = value.get("service_tier")
            tier, inferred = _pricing_tier([observed_tier], model, None)
            pricing_evidence = {"tier": tier, "basis": (
                "Tier inferred from the model default; control_call.service_tier omitted/null"
                if inferred else "controller control_call.service_tier only")}
            rate, pricing_ref = select(pricing, model, tier)
            if i is not None and i > 272000:
                rate, pricing_ref = None, None
            usd = None
            if rate and all(v is not None for v in (i, c, o)) and i <= 272000:
                usd = ((i - c) * rate["input_per_million_usd"] +
                       c * rate["cached_input_per_million_usd"] +
                       o * rate["output_per_million_usd"]) / 1_000_000
            successful |= value.get("status") == "success"
            calls.append({"call_id": f"{task_id}-control-{len(calls) + 1}", "purpose": purpose,
                          "backend": backend, "model": model,
                          "status": "timeout" if process.get("timed_out") else
                                    "completed" if value.get("status") == "success" else "failed",
                          "usage": {**counts, "usd": usd, "latency_seconds": value.get("latency_seconds"),
                                    "cost_basis": "api_equivalent_usd",
                                    "pricing_ref": pricing_ref}})
            if provenance is not None:
                provenance.append({"call_id": calls[-1]["call_id"], "observed_service_tier": observed_tier,
                    "pricing_evidence": pricing_evidence, "basis": pricing_evidence["basis"],
                    "pricing_ref": pricing_ref,
                    "stderr_sha256": pinned[name],
                    "record_sha256": digest(json.dumps(value, sort_keys=True).encode())})
        exit_code = process.get("exit_code")
        if (type(exit_code) is not int or exit_code < 0 or process.get("timed_out") or
                (exit_code != 0 and len(calls) == count_before and not delegations)):
            complete = False
        if purpose != "judge" and exit_code == 0 and not successful:
            complete = False
        if purpose == "judge":
            if len(calls) > count_before and not delegations:
                complete = False
            if delegations and sum(d.get("forwarded_control_calls", 0) for d in delegations) != len(calls) - count_before:
                complete = False
            contract_name = str(Path(name).parent / "contract.json")
            contract_text = read(contract_name)
            if not delegations and contract_text:
                criteria = json.loads(contract_text).get("success_criteria", [])
                judges = [c for c in criteria if c["check"]["type"] == "llm_judge"]
                if judges and len(judges) != len(criteria):
                    verdict_text = read(str(Path(name).with_suffix(".json")))
                    try:
                        items = json.loads(verdict_text)["items"] if verdict_text else []
                        by_id = {item["id"]: item for item in items}
                        budget_skipped = all(
                            by_id[c["id"]]["status"] == "unverifiable" and
                            by_id[c["id"]]["evidence"] ==
                            "criterion not started: HARNESS_VERIFY_BUDGET_SECONDS exhausted"
                            for c in judges)
                    except (ValueError, KeyError, TypeError):
                        budget_skipped = False
                    if not budget_skipped:
                        complete = False
    return calls, total([c["usage"]["usd"] for c in calls]) if complete and streams else None
