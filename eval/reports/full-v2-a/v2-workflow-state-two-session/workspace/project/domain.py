from __future__ import annotations

def resolve(rows: list[dict[str, str | int]]) -> dict:
    if any(r['value'] not in {0, 1, 2} for r in rows):
        raise ValueError('workflow-state: invalid state')
    states: dict[str, int] = {}
    for row in rows:
        key, value = row['target'], row['value']
        previous = states.get(key)
        if (previous is None and value != 0) or (
            previous is not None and value not in (previous, previous + 1)
        ):
            raise ValueError('workflow-state: invalid transition')
        states[key] = value
    return {'states': dict(sorted(states.items()))}
