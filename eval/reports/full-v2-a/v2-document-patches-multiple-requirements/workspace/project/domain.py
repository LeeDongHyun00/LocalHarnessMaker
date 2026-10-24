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
    offsets = {key: sorted(groups[key], reverse=True) for key in sorted(groups)}
    patches = {key: [groups[key][pos] for pos in positions] for key, positions in offsets.items()}
    return {'patches': patches, 'offsets': offsets}
