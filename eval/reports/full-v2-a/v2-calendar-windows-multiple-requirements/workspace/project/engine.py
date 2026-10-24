from __future__ import annotations
from .validation import validate
from .domain import resolve
from .policy import PREFIX

def compute(rows: list[dict[str, str | int]]) -> dict:
    canonical = validate(rows)
    selected: dict[str, dict[str, str | int]] = {}
    for row in canonical:
        key = row['id']
        # Replacing a value preserves the id's first insertion position.
        selected[key] = row
    return resolve(list(selected.values()))
