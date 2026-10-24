from __future__ import annotations
from collections import deque

def resolve(rows: list[dict[str, str | int]]) -> dict:
    if any(r['value'] < 0 for r in rows):
        raise ValueError('cache-invalidation: negative generation')
    parents = {r['id']: r['target'] for r in rows}
    if any(p not in parents for p in parents.values()):
        raise ValueError('cache-invalidation: missing dependency')
    dirty = {r['id'] for r in rows if r['value'] == 0}
    children: dict[str, list[str]] = {key: [] for key in parents}
    ready: deque[str] = deque()
    for key, parent in parents.items():
        if key == parent:
            ready.append(key)
        else:
            children[parent].append(key)
    visited = 0
    while ready:
        key = ready.popleft()
        visited += 1
        for child in children[key]:
            if key in dirty:
                dirty.add(child)
            ready.append(child)
    if visited != len(parents):
        raise ValueError('cache-invalidation: cycle')
    return {'dirty': sorted(dirty), 'clean': sorted(set(parents) - dirty)}
