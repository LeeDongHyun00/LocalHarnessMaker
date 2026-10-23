from __future__ import annotations

def resolve(rows: list[dict[str, str | int]]) -> dict:
    if any(any(part in {'', '.'} for part in r['id'].split('/')) for r in rows):
        raise ValueError('filesystem-manifests: invalid path')
    if any(r['value'] < 0 for r in rows):
        raise ValueError('filesystem-manifests: negative size')
    return {'files': {r['id']: {'digest': r['target'], 'size': r['value']} for r in sorted(rows, key=lambda r: r['id'])}, 'bytes': sum(r['value'] for r in rows)}
