"""Read-only handoff validation without a contract or model calls."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import ValidationError

from verifier.schema import validate


class HandoffInputError(ValueError):
    """The supplied handoff cannot be read or is invalid."""


def validate_handoff(path: Path) -> None:
    """Validate the schema and reject contradictory criterion states."""
    try:
        handoff = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HandoffInputError(f"cannot read handoff {path}: {exc}") from exc
    try:
        validate(handoff, "handoff.schema.json")
    except ValidationError as exc:
        raise HandoffInputError(f"invalid handoff: {exc}") from exc
    done_ids = {item["criterion_id"] for item in handoff["done"]}
    remaining_ids = {item["criterion_id"] for item in handoff["remaining"]}
    overlap = done_ids & remaining_ids
    if overlap:
        raise HandoffInputError(
            "criterion_id appears in both done and remaining: " + ", ".join(sorted(overlap))
        )
