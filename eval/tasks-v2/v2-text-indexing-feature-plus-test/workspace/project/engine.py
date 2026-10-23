from __future__ import annotations
from .validation import validate
from .domain import resolve
from .policy import PREFIX

def compute(rows: list[dict[str, str | int]]) -> dict:
    canonical = validate(rows)
    selected: dict[str, dict[str, str | int]] = {}
    for row in canonical:
        key = row['id']
        if key in selected:
            previous = selected[key]
            if row['value'] == previous['value'] and row['target'] != previous['target']:
                raise ValueError(PREFIX + ': ambiguous id')
            if row['value'] < previous['value']:
                continue
        selected[key] = row
    return resolve(list(selected.values()))
