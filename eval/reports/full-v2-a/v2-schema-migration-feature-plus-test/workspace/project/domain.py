from __future__ import annotations

def resolve(rows: list[dict[str, str | int]]) -> dict:
    if any(r['value'] <= 0 for r in rows):
        raise ValueError('schema-migration: invalid version')
    versions = {r['id']: r['value'] for r in rows}
    if any(r['target'] not in versions for r in rows):
        raise ValueError('schema-migration: missing predecessor')
    if any(r['id'] != r['target'] and versions[r['target']] >= r['value'] for r in rows):
        raise ValueError('schema-migration: version order')
    return {'migrations': [r['id'] for r in sorted(rows, key=lambda r: (r['value'], r['id']))]}
