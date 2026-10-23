from . import policy

def validate(rows: list[dict]) -> list[dict]:
    if not isinstance(rows, list):
        raise TypeError('ledger: rows must be a list')
    result: list[dict] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(['id', 'account', 'amount']):
            raise ValueError('ledger: invalid row')
        if any(not isinstance(row[key], str) or not row[key].strip() for key in ['id', 'account']):
            raise ValueError('ledger: invalid row')
        if any(type(row[key]) is not int for key in ['amount']):
            raise ValueError('ledger: invalid row')
        result.append({
            'id': policy.normalize(row['id']),
            'account': policy.normalize(row['account']),
            'amount': row['amount'],
        })
    return result
