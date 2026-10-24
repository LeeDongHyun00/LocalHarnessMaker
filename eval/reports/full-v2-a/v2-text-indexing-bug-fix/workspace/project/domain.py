from __future__ import annotations

def resolve(rows: list[dict[str, str | int]]) -> dict:
    if any(r['value'] < 0 for r in rows):
        raise ValueError('text-indexing: negative count')
    groups: dict[str, list[dict[str, str | int]]] = {}
    for row in rows:
        groups.setdefault(row['target'], []).append(row)
    return {'index': {key: {'count': sum(r['value'] for r in groups[key]), 'documents': [r['id'] for r in groups[key]]} for key in sorted(groups)}}
