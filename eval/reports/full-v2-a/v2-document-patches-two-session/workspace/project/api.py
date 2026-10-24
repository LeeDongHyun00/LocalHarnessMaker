from __future__ import annotations
import json
from . import engine
from .policy import PREFIX

def run(rows: list[dict[str, str | int]]) -> dict:
    return engine.compute(rows)

def render(rows: list[dict[str, str | int]]) -> str:
    return json.dumps(engine.compute(rows), ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'

def run_many(batches: list[list[dict[str, str | int]]]) -> list[dict]:
    if not isinstance(batches, list):
        raise TypeError(PREFIX + ': batches must be a list')
    return [run(rows) for rows in batches]

def render_many(batches: list[list[dict[str, str | int]]]) -> str:
    if not isinstance(batches, list):
        raise TypeError(PREFIX + ': batches must be a list')
    return ''.join(render(rows) for rows in batches)
