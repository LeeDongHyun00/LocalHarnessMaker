from __future__ import annotations

def resolve(rows: list[dict[str, str | int]]) -> dict:
    if any(not 0 <= r['value'] <= 23 for r in rows):
        raise ValueError('calendar-windows: invalid hour')
    groups: dict[str, dict[int, str]] = {}
    for row in rows:
        hours = groups.setdefault(row['target'], {})
        if row['value'] in hours:
            raise ValueError('calendar-windows: overlap')
        hours[row['value']] = row['id']
    return {'rooms': {key: [[start, start + 1, who] for start, who in sorted(groups[key].items())] for key in sorted(groups)}}
