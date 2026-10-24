from __future__ import annotations
from .policy import PREFIX

def resolve(rows: list[dict[str, str | int]]) -> dict:
    if any(r['value'] < 0 for r in rows):
        raise ValueError(PREFIX + ': negative offset')
    groups: dict[str, dict[int, str]] = {}
    for row in rows:
        positions = groups.setdefault(row['target'], {})
        if row['value'] in positions:
            raise ValueError(PREFIX + ': collision')
        positions[row['value']] = row['id']
    return {'patches': {key: [groups[key][pos] for pos in sorted(groups[key], reverse=True)] for key in sorted(groups)}, 'offsets': {key: sorted(groups[key], reverse=True) for key in sorted(groups)}}
