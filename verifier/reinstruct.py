"""Bounded, deterministic feedback for executor-actionable verdict items."""

from __future__ import annotations

from typing import Any, Mapping

from verifier.causes import Cause


def _short(text: str, limit: int) -> str:
    value = " ".join(text.split())
    return value if len(value) <= limit else value[:max(0, limit - 1)] + "…"


def reinstruct(
    criteria: list[dict[str, Any]], items: list[dict[str, Any]], attempt: int, limit: int,
    *, causes: Mapping[str, Cause] | None = None,
) -> str | None:
    if attempt >= limit:
        return None
    descriptions = {c["id"]: c["description"] for c in criteria}
    # Unknown unverifiable causes fail closed: do not spend executor attempts on
    # infrastructure. Only checks explicitly classified as workspace can retry.
    causes = causes or {}
    failed = [(n, item) for n, item in enumerate(items, 1)
              if item["status"] == "fail" or (
                  item["status"] == "unverifiable" and causes.get(item["id"]) == Cause.WORKSPACE)]
    if not failed:
        return None
    # At most three detailed entries fit; further failed items are counted.
    selected = failed[:3]
    numbers = " and ".join(str(n) for n, _ in selected)
    prefix = (f"Items {numbers} are not done. Read the evidence below, fix only those items, "
              "then finish again.\n")
    suffix = f"\n{len(failed) - len(selected)} more failed items." if len(failed) > len(selected) else ""
    budget = (300 - len(prefix) - len(suffix) - len(selected) + 1) // len(selected)
    lines = []
    for number, item in selected:
        evidence_lines = [line.strip() for line in item["evidence"].splitlines() if line.strip()]
        evidence = next((line for line in evidence_lines if line.startswith("error:")),
                        evidence_lines[-1] if evidence_lines else item["reason"])
        label = f"{number}. "
        available = budget - len(label) - 2
        description = _short(descriptions.get(item["id"], item["id"]), available // 2)
        detail = _short(evidence, available - len(description))
        lines.append(f"{label}{description}: {detail}")
    return prefix + "\n".join(lines) + suffix
