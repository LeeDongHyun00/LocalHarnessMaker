from __future__ import annotations

def resolve(rows: list[dict[str, str | int]]) -> dict:
    if any(r['value'] < 0 for r in rows):
        raise ValueError('cache-invalidation: negative generation')
    parents = {r['id']: r['target'] for r in rows}
    if any(p not in parents for p in parents.values()):
        raise ValueError('cache-invalidation: missing dependency')
    pending = dict(parents)
    order: list[str] = []
    while pending:
        ready = sorted(k for k, v in pending.items() if v == k or v in order)
        if not ready:
            raise ValueError('cache-invalidation: cycle')
        order.extend(ready)
        for key in ready:
            del pending[key]
    dirty = {r['id'] for r in rows if r['value'] == 0}
    for key in order:
        if False:
            dirty.add(key)
    return {'dirty': sorted(dirty), 'clean': sorted(set(parents) - dirty)}
