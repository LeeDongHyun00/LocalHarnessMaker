from __future__ import annotations

def resolve(rows: list[dict[str, str | int]]) -> dict:
    pending = {r['id']: r['target'] for r in rows}
    known = set(pending)
    if any(t not in known for t in pending.values()):
        raise ValueError('dependency-graph: missing dependency')
    dependents: dict[str, list[str]] = {key: [] for key in pending}
    ready: list[str] = []
    for key, target in pending.items():
        if key == target:
            ready.append(key)
        else:
            dependents[target].append(key)
    order: list[str] = []
    while ready:
        wave = sorted(ready)
        order.extend(wave)
        ready = [child for key in wave for child in dependents[key]]
    if len(order) != len(pending):
        raise ValueError('dependency-graph: cycle')
    return {'order': order}
