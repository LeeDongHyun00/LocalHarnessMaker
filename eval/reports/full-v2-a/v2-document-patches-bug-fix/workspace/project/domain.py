from __future__ import annotations

def resolve(rows: list[dict[str, str | int]]) -> dict:
    if any(r['value'] < 0 for r in rows):
        raise ValueError('document-patches: negative offset')
    groups: dict[str, dict[int, str]] = {}
    for row in rows:
        positions = groups.setdefault(row['target'], {})
        if row['value'] in positions:
            raise ValueError('document-patches: collision')
        positions[row['value']] = row['id']
    return {'patches': {key: [groups[key][pos] for pos in sorted(groups[key], reverse=True)] for key in sorted(groups)}, 'offsets': {key: sorted(groups[key], reverse=True) for key in sorted(groups)}}
