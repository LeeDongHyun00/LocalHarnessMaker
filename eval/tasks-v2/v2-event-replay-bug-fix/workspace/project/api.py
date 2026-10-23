from __future__ import annotations
import json
from . import engine
from .policy import PREFIX

def run(rows: list[dict[str, str | int]]) -> dict:
    return _legacy_run(rows)

def render(rows: list[dict[str, str | int]]) -> str:
    return json.dumps(_legacy_render(rows), ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'

def run_many(batches: list[list[dict[str, str | int]]]) -> list[dict]:
    if not isinstance(batches, list):
        raise TypeError(PREFIX + ': batches must be a list')
    return [engine.compute(rows) for rows in batches]

def render_many(batches: list[list[dict[str, str | int]]]) -> str:
    if not isinstance(batches, list):
        raise TypeError(PREFIX + ': batches must be a list')
    return ''.join(render(rows) for rows in batches)

from .validation import validate
from .domain import resolve
from .policy import PREFIX

def _legacy_run(rows: list[dict[str, str | int]]) -> dict:
    canonical = validate(rows)
    selected: dict[str, dict[str, str | int]] = {}
    for row in canonical:
        key = row['id']
        if key in selected and selected[key] != row:
            raise ValueError(PREFIX + ': duplicate id')
        selected[key] = row
    return resolve(list(selected.values()))
def _legacy_render(rows: list[dict[str, str | int]]) -> dict:
    canonical = validate(rows)
    selected: dict[str, dict[str, str | int]] = {}
    for row in canonical:
        key = row['id']
        if key in selected and selected[key] != row:
            raise ValueError(PREFIX + ': duplicate id')
        selected[key] = row
    return resolve(list(selected.values()))
