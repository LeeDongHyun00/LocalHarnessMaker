from __future__ import annotations

def resolve(rows: list[dict[str, str | int]]) -> dict:
    groups: dict[str, list[dict[str, str | int]]] = {}
    for row in rows:
        groups.setdefault(row['target'], []).append(row)
    facets = [{'name': key, 'count': len(group), 'score': sum(r['value'] for r in group), 'ids': sorted(r['id'] for r in group)} for key, group in groups.items()]
    return {'facets': sorted(facets, key=lambda f: (f['name'],))}
