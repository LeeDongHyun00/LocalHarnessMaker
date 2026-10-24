from __future__ import annotations

def resolve(rows: list[dict[str, str | int]]) -> dict:
    if any(not 0 <= r['value'] <= 100 for r in rows):
        raise ValueError('rate-budgets: invalid cost')
    totals: dict[str, int] = {}
    for row in rows:
        key = row['target']
        totals[key] = totals.get(key, 0) + row['value']
    if any(v > 100 for v in totals.values()):
        raise ValueError('rate-budgets: exhausted')
    return {'remaining': {key: 100 - totals[key] for key in sorted(totals)}}
