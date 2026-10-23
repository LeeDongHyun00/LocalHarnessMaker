from . import policy

def validate(rows: list[dict]) -> list[dict]:
    if not isinstance(rows, list):
        raise TypeError('routing: rows must be a list')
    result: list[dict] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(['path', 'target', 'priority']):
            raise ValueError('routing: invalid row')
        if any(not isinstance(row[key], str) or not row[key].strip() for key in ['path', 'target']):
            raise ValueError('routing: invalid row')
        if any(type(row[key]) is not int for key in ['priority']):
            raise ValueError('routing: invalid row')
        result.append(dict(row))
    # Finish field validation before applying any domain policy.
    for item in result:
        item['path'] = policy.normalize(item['path'])
        item['target'] = item['target'].strip().casefold()
    return result
