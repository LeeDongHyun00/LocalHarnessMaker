from .validation import validate

def compute(rows: list[dict]) -> dict:
    rows = validate(rows)
    selected: dict[str, dict] = {}
    for row in rows:
        path = row['path']
        if path not in selected or row['priority'] >= selected[path]['priority']:
            selected[path] = dict(row)
    rules = sorted(selected.values(), key=lambda row: (-row['priority'], -len(row['path']), row['path']))
    return {'rules': rules, 'targets': sorted({row['target'] for row in rules})}
