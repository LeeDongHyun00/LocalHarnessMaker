from __future__ import annotations
from .validation import validate
from .domain import resolve

def compute(rows: list[dict[str, str | int]]) -> dict:
    canonical = validate(rows)
    selected: dict[str, dict[str, str | int]] = {}
    for row in canonical:
        key = row['id']
        # Replacing an existing key preserves its first encounter position.
        selected[key] = row
    return resolve(list(selected.values()))
