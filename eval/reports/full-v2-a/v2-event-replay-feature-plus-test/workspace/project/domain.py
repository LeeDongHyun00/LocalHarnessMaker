from __future__ import annotations

def resolve(rows: list[dict[str, str | int]]) -> dict:
    balances: dict[str, int] = {}
    history: list[int] = []
    for row in rows:
        key = row['target']
        balances[key] = balances.get(key, 0) + row['value']
        if balances[key] < 0:
            raise ValueError('event-replay: negative prefix')
        history.append(balances[key])
    return {'balances': dict(sorted(balances.items())), 'history': history}
