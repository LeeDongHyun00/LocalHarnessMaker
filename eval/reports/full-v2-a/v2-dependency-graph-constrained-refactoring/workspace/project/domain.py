from __future__ import annotations

def resolve(rows: list[dict[str, str | int]]) -> dict:
    pending = {r['id']: r['target'] for r in rows}
    known = set(pending)
    if any(t not in known for t in pending.values()):
        raise ValueError('dependency-graph: missing dependency')
    order: list[str] = []
    while pending:
        ready = sorted(k for k, v in pending.items() if v == k or v in order)
        if not ready:
            raise ValueError('dependency-graph: cycle')
        order.extend(ready)
        for key in ready:
            del pending[key]
    return {'order': order}
