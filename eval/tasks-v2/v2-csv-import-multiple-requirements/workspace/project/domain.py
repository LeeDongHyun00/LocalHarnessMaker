from __future__ import annotations

def resolve(rows: list[dict[str, str | int]]) -> dict:
    columns = list(dict.fromkeys(r['target'] for r in rows))
    return {'columns': columns, 'data': [[r['value'] for r in rows if r['target'] == key] for key in columns], 'ids': [[r['id'] for r in rows if r['target'] == key] for key in columns]}
