"""Resolve observed tiers against pinned, schema-compatible price provenance."""

import json
from pathlib import Path
from typing import Any

CATALOG_PREFIX = "Pinned tier snapshots: "


def snapshots(pricing: dict[str, Any]) -> list[dict[str, Any]]:
    """Read an offline catalog or its closed-schema report representation."""
    if pricing.get("source", "").startswith(CATALOG_PREFIX):
        return json.loads(pricing["source"][len(CATALOG_PREFIX):])
    return [{k: v for k, v in pricing.items() if k != "snapshots"}, *pricing.get("snapshots", [])]


def report_pricing(pricing: dict[str, Any]) -> dict[str, Any]:
    """Pin every tier's full rates in the existing metadata source field."""
    catalog = snapshots(pricing)
    if len(catalog) == 1:
        return catalog[0]
    return {"snapshot_id": pricing["snapshot_id"], "checked_on": max(s["checked_on"] for s in catalog),
            "source": CATALOG_PREFIX + json.dumps(catalog, sort_keys=True), "rates": catalog[0]["rates"]}


def select(pricing: dict[str, Any], model: str, tier: Any) -> tuple[dict[str, Any] | None, str | None]:
    """Unknown/missing tiers never inherit requested settings or Standard rates."""
    if tier in ("priority", "fast"):
        candidates = [s for s in snapshots(pricing) if "-fast-" in s["snapshot_id"]]
    elif tier == "standard":
        candidates = [s for s in snapshots(pricing) if "-fast-" not in s["snapshot_id"]]
    else:
        return None, None
    for snapshot in candidates:
        rate = next((r for r in snapshot["rates"] if r["model"] == model), None)
        if rate:
            return rate, snapshot["snapshot_id"]
    return None, None


def extends(current: dict[str, Any], recorded: dict[str, Any]) -> bool:
    """Allow added snapshots only when every historical pin remains identical."""
    available = {s["snapshot_id"]: s for s in snapshots(current)}
    return all(available.get(s["snapshot_id"]) == s for s in snapshots(recorded))


def retained_provenance(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Read an existing task's pinned call-level price evidence without repricing."""
    from pathlib import Path
    from eval.runner.audit import digest
    from eval.runner.publication import evidence_path

    refs = [a for a in task.get("artifacts", []) if Path(a["path"]).name == "pricing-provenance.json"]
    if not refs:
        return []
    if len(refs) != 1:
        raise ValueError("Duplicate pricing provenance")
    path = evidence_path(refs[0]["path"])
    if digest(path.read_bytes()) != refs[0]["sha256"]:
        raise ValueError("Pricing provenance hash mismatch")
    return json.loads(path.read_text())


def preserve_provenance(task: dict[str, Any], directory: Path, *, prior: dict[str, Any],
                        additional: list[dict[str, Any]] | None = None) -> None:
    """Keep historical accounting distinct from fresh continuation observations."""
    from pathlib import Path
    from eval.runner.report import artifact

    current = {row["call_id"]: row for row in retained_provenance(task)}
    current.update({row["call_id"]: row for row in additional or []})
    previous = {row["call_id"]: row for row in retained_provenance(prior)}
    historical = {call["call_id"] for call in prior["calls"]}
    rows = []
    for call in task["calls"]:
        identity = call["call_id"]
        row = previous.get(identity) if identity in historical else current.get(identity)
        if row is None:
            row = {"call_id": identity, "observed_service_tier": None,
                   "basis": "Retained original accounting; no per-call tier observation available."}
        rows.append(dict(row, pricing_ref=call["usage"]["pricing_ref"]))
    path = directory / "pricing-provenance.json"
    path.write_text(json.dumps(rows, indent=2) + "\n")
    task["artifacts"] = [a for a in task["artifacts"] if Path(a["path"]).name != path.name] + [artifact(path)]
