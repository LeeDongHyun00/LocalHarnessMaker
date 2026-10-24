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


def snapshot_hashes(pricing: dict[str, Any]) -> dict[str, str]:
    """Hash each complete snapshot independently of its enclosing catalog."""
    from eval.runner.audit import digest

    pins: dict[str, str] = {}
    for snapshot in snapshots(pricing):
        identity = snapshot["snapshot_id"]
        value = digest(json.dumps(snapshot, sort_keys=True).encode())
        if identity in pins and pins[identity] != value:
            raise ValueError("Conflicting pricing snapshots")
        pins[identity] = value
    return pins


def pin_provenance(rows: list[dict[str, Any]], pricing: dict[str, Any]) -> list[dict[str, Any]]:
    """Bind each call to its own snapshot, including mixed historical tiers."""
    pins = snapshot_hashes(pricing)
    result = []
    for row in rows:
        reference = row.get("pricing_ref")
        if reference is not None and reference not in pins:
            raise ValueError("Call pricing snapshot unavailable")
        result.append(dict(row, pricing_snapshot_sha256=pins.get(reference)))
    return result


def retained_provenance(task: dict[str, Any], pricing: dict[str, Any] | None = None) -> list[dict[str, Any]]:
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
        # Older continuation builds overwrote unselected tasks' provenance
        # while retaining the report's original artifact pin. Recover only the
        # exact legacy fallback bytes that reproduce that historical SHA-256;
        # never adopt the overwritten file or replace a historical hash.
        rows = [{"call_id": call["call_id"], "observed_service_tier": None,
                 "basis": "Retained original accounting; no per-call tier observation available.",
                 "pricing_ref": call["usage"]["pricing_ref"]} for call in task["calls"]]
        if digest((json.dumps(rows, indent=2) + "\n").encode()) != refs[0]["sha256"]:
            raise ValueError("Pricing provenance hash mismatch")
    else:
        rows = json.loads(path.read_text())
    if pricing is not None:
        pins = snapshot_hashes(pricing)
        for row in rows:
            if row.get("pricing_snapshot_sha256") is not None and (
                    pins.get(row.get("pricing_ref")) != row["pricing_snapshot_sha256"]):
                raise ValueError("Pricing snapshot hash mismatch")
    return rows


def preserve_provenance(task: dict[str, Any], directory: Path, *, prior: dict[str, Any],
                        pricing: dict[str, Any],
                        additional: list[dict[str, Any]] | None = None) -> None:
    """Keep historical accounting distinct from fresh continuation observations."""
    from pathlib import Path
    from eval.runner.report import artifact

    current = {row["call_id"]: row for row in retained_provenance(task, pricing)}
    current.update({row["call_id"]: row for row in additional or []})
    previous = {row["call_id"]: row for row in retained_provenance(prior, pricing)}
    historical = {call["call_id"] for call in prior["calls"]}
    old_calls = {call["call_id"]: call for call in prior["calls"]}
    rows = []
    for call in task["calls"]:
        identity = call["call_id"]
        row = previous.get(identity) if identity in historical else current.get(identity)
        if (identity in old_calls and old_calls[identity]['usage']['usd'] is None
                and call['usage']['usd'] is not None):
            row = current.get(identity)
        if row is None:
            row = {"call_id": identity, "observed_service_tier": None,
                   "basis": "Retained original accounting; no per-call tier observation available."}
        rows.append(dict(row, pricing_ref=call["usage"]["pricing_ref"]))
    path = directory / "pricing-provenance.json"
    path.write_text(json.dumps(pin_provenance(rows, pricing), indent=2) + "\n")
    task["artifacts"] = [a for a in task["artifacts"] if Path(a["path"]).name != path.name] + [artifact(path)]


def recover_default_tiers(entry: dict[str, Any], config: dict[str, Any]) -> None:
    """Recover omitted applied tiers from legacy per-process exit captures only."""
    from eval.runner.telemetry import _pricing_tier

    for segment in entry['segments']:
        evidence = segment.get('pricing_evidence', {})
        observations = evidence.get('records', [])
        if (evidence.get('tier') == 'unknown' and observations and segment.get('settings_verified') is True
                and all('observed_service_tier' in row and row['observed_service_tier'] is None
                        for row in observations)):
            tier, inferred = _pricing_tier([None], config['model'], config.get('service_tier'))
            if inferred:
                segment['pricing_evidence'] = dict(evidence, tier=tier,
                    basis='Tier inferred from the model default during regrade; retained applied service_tier omitted/null')


def merge_regraded_accounting(task: dict[str, Any], prior: dict[str, Any]) -> None:
    """Keep priced history; fill only complete, newly resolved retained usage."""
    import copy
    from eval.metrics import total

    rebuilt = {c['call_id']: c for c in task['calls']}
    complete_control = task['costs']['control_usd'] is not None
    calls = copy.deepcopy(prior['calls'])
    for call in calls:
        candidate = rebuilt.get(call['call_id'])
        if (candidate and call['usage']['usd'] is None and candidate['usage']['usd'] is not None
                and all(call['usage'][k] == candidate['usage'][k]
                        for k in ('input_tokens', 'cached_input_tokens', 'output_tokens'))):
            call['usage'] = copy.deepcopy(candidate['usage'])
    task['calls'] = calls
    executor = total([c['usage']['usd'] for c in calls if c['purpose'] == 'executor'])
    control = (total([c['usage']['usd'] for c in calls if c['purpose'] != 'executor'])
               if complete_control else prior['costs']['control_usd'])
    task['costs'] = {'executor_usd': executor, 'control_usd': control,
                     'total_usd': total([executor, control])}
