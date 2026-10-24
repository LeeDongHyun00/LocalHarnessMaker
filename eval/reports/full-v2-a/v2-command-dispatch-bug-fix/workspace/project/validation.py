from __future__ import annotations
from .policy import normalize, PREFIX

def validate(rows: list[dict[str, str | int]]) -> list[dict[str, str | int]]:
    if not isinstance(rows, list):
        raise TypeError(PREFIX + ': rows must be a list')
    result: list[dict[str, str | int]] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {'id', 'target', 'value'}:
            raise ValueError(PREFIX + ': invalid row')
        if not isinstance(row['id'], str) or not isinstance(row['target'], str) or type(row['value']) is not int:
            raise ValueError(PREFIX + ': invalid row')
        if not row['id'].strip() or not row['target'].strip():
            raise ValueError(PREFIX + ': invalid row')
        result.append({'id': normalize(row['id']), 'target': normalize(row['target']), 'value': row['value']})
    return result
