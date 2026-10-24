import json
from .engine import compute

def render(rows: list[dict]) -> str:
    return json.dumps(compute(rows), ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
