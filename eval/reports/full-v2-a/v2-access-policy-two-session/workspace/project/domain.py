from __future__ import annotations

def resolve(rows: list[dict[str, str | int]]) -> dict:
    groups: dict[str, list[dict[str, str | int]]] = {}
    for row in rows:
        groups.setdefault(row['target'], []).append(row)
    result: dict[str, dict[str, str | bool]] = {}
    for key in sorted(groups):
        winner = min(groups[key], key=lambda r: (-abs(r['value']), r['value'] > 0, r['id']))
        result[key] = {'rule': winner['id'], 'allow': winner['value'] > 0}
    return {'decisions': result}
