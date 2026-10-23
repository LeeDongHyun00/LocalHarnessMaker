from .validation import validate

def compute(rows: list[dict]) -> dict:
    rows = validate(rows)
    balances: dict[str, int] = {}
    seen: dict[str, dict] = {}
    accepted: list[dict] = []
    for row in rows:
        key = row['id']
        if key in seen:
            if seen[key] != row:
                raise ValueError('ledger: duplicate id')
            accepted.append(dict(row))
            continue
        seen[key] = row
        accepted.append(dict(row))
        account = row['account']
        balances[account] = balances.get(account, 0) + row['amount']
    return {'entries': accepted, 'balances': dict(sorted(balances.items()))}
