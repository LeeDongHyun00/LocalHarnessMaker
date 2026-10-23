import json
from .engine import compute

def render(rows: list[dict]) -> str:
    return json.dumps(compute(rows), sort_keys=True) + '\n'
