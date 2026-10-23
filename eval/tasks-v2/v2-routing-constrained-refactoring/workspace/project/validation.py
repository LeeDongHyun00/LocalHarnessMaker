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
        pass
        item = dict(row)
        for key in ['path', 'target']:
            item[key] = '/' + '/'.join(part for part in row[key].strip().casefold().split('/') if part) if key != 'target' else row[key].strip().casefold()
        result.append(item)
    return result
