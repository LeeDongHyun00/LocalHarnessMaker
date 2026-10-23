from . import policy

def validate(rows: list[dict]) -> list[dict]:
    if not isinstance(rows, list):
        raise TypeError('reservations: rows must be a list')
    result: list[dict] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(['id', 'resource', 'start', 'end']):
            raise ValueError('reservations: invalid row')
        if any(not isinstance(row[key], str) or not row[key].strip() for key in ['id', 'resource']):
            raise ValueError('reservations: invalid row')
        if any(not isinstance(row[key], int) or isinstance(row[key], bool) for key in ['start', 'end']):
            raise ValueError('reservations: invalid row')
        if row['start'] < 0 or row['start'] >= row['end']:
            raise ValueError('reservations: invalid row')
        item = dict(row)
        for key in ['id', 'resource']:
            item[key] = policy.normalize(row[key])
        result.append(item)
    return result
