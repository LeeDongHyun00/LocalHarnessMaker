from . import policy

def validate(rows: list[dict]) -> list[dict]:
    if not isinstance(rows, list):
        raise TypeError('inventory: rows must be a list')
    result: list[dict] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(['sku', 'location', 'delta']):
            raise ValueError('inventory: invalid row')
        if any(not isinstance(row[key], str) or not row[key].strip() for key in ['sku', 'location']):
            raise ValueError('inventory: invalid row')
        if any(type(row[key]) is not int for key in ['delta']):
            raise ValueError('inventory: invalid row')
        item = dict(row)
        for key in ['sku', 'location']:
            item[key] = policy.normalize(row[key])
        result.append(item)
    return result
