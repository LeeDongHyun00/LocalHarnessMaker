from .validation import validate

def compute(rows: list[dict]) -> dict:
    rows = validate(rows)
    balances: dict[str, int] = {}
    seen: dict[str, dict] = {}
    accepted: list[dict] = []
    for row in rows:
        key = row['id']
        if key in seen:
            if seen[key]['account'] != row['account']:
                raise ValueError('ledger: duplicate id')
            seen[key]['amount'] = row['amount']
            continue
        entry = dict(row)
        seen[key] = entry
        accepted.append(entry)
    for row in accepted:
        account = row['account']
        balances[account] = balances.get(account, 0) + row['amount']
    return {'entries': accepted, 'balances': dict(sorted(balances.items()))}
