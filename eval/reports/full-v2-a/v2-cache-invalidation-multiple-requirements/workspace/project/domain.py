from __future__ import annotations

def resolve(rows: list[dict[str, str | int]]) -> dict:
    if any(r['value'] < 0 for r in rows):
        raise ValueError('cache-invalidation: negative generation')
    parents = {r['id']: r['target'] for r in rows}
    if any(p not in parents for p in parents.values()):
        raise ValueError('cache-invalidation: missing dependency')
    # Walk dependency chains iteratively so deep graphs need no recursion.
    visited: set[str] = set()
    order: list[str] = []
    for start in parents:
        path: list[str] = []
        active: set[str] = set()
        key = start
        while key not in visited:
            if key in active:
                raise ValueError('cache-invalidation: cycle')
            active.add(key)
            path.append(key)
            parent = parents[key]
            if parent == key:
                break
            key = parent
        visited.update(path)
        order.extend(reversed(path))
    dirty = {r['id'] for r in rows if r['value'] == 0}
    for key in order:
        if parents[key] in dirty:
            dirty.add(key)
    return {'dirty': sorted(dirty), 'clean': sorted(set(parents) - dirty)}
