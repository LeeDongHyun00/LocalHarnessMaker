from __future__ import annotations
from .policy import PREFIX

def resolve(rows: list[dict[str, str | int]]) -> dict:
    if any(r['value'] < 0 for r in rows):
        raise ValueError(PREFIX + ': negative generation')
    parents = {r['id']: r['target'] for r in rows}
    if any(p not in parents for p in parents.values()):
        raise ValueError(PREFIX + ': missing dependency')
    resolved: set[str] = set()
    order: list[str] = []
    for start in parents:
        path: list[str] = []
        visiting: set[str] = set()
        key = start
        while key not in resolved:
            if key in visiting:
                raise ValueError(PREFIX + ': cycle')
            visiting.add(key)
            path.append(key)
            if parents[key] == key:
                break
            key = parents[key]
        # Dependencies precede dependents, without recursion depth limits.
        order.extend(reversed(path))
        resolved.update(path)
    dirty = {r['id'] for r in rows if r['value'] == 0}
    for key in order:
        if parents[key] in dirty:
            dirty.add(key)
    return {'dirty': sorted(dirty), 'clean': sorted(set(parents) - dirty)}
