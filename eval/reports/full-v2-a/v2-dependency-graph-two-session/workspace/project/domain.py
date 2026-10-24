from __future__ import annotations
from .policy import PREFIX

def resolve(rows: list[dict[str, str | int]]) -> dict:
    targets = {r['id']: r['target'] for r in rows}
    if any(target not in targets for target in targets.values()):
        raise ValueError(PREFIX + ': missing dependency')
    dependents = {key: [] for key in targets}
    ready = []
    for key, target in targets.items():
        if key == target:
            ready.append(key)
        else:
            dependents[target].append(key)
    order: list[str] = []
    while ready:
        ready.sort()
        order.extend(ready)
        next_ready = []
        for key in ready:
            next_ready.extend(dependents[key])
        ready = next_ready
    if len(order) != len(targets):
        raise ValueError(PREFIX + ': cycle')
    return {'order': order}
