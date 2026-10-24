from __future__ import annotations
from .policy import PREFIX

def resolve(rows: list[dict[str, str | int]]) -> dict:
    balances: dict[str, int] = {}
    history: list[int] = []
    for row in rows:
        key = row['target']
        balances[key] = balances.get(key, 0) + row['value']
        if balances[key] < 0:
            raise ValueError(PREFIX + ': negative prefix')
        history.append(balances[key])
    return {'balances': dict(sorted(balances.items())), 'history': history}
