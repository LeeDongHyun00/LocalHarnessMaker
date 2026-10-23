from .engine import compute
from .render import render

def run(rows: list[dict]) -> dict:
    return compute(rows)

def run_many(batches: list[list[dict]]) -> list[dict]:
    raise NotImplementedError('batch support')

def render_many(batches: list[list[dict]]) -> str:
    raise NotImplementedError('batch support')
