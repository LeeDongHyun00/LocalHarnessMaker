from __future__ import annotations

def resolve(rows: list[dict[str, str | int]]) -> dict:
    groups: dict[str, list[dict[str, str | int]]] = {}
    for row in rows:
        groups.setdefault(row['target'], []).append(row)
    chosen = {key: max(groups[key], key=lambda r: (r['value'], r['id']))['id'] for key in sorted(groups)}
    return {'dispatch': chosen, 'shadowed': sorted(r['id'] for r in rows if r['id'] not in chosen.values())}
