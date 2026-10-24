from .validation import validate

def compute(rows: list[dict]) -> dict:
    rows = validate(rows)
    selected: dict[str, dict] = {}
    for row in rows:
        path = row['path']
        if (path not in selected
                or row['priority'] > selected[path]['priority']
                or (row['priority'] == selected[path]['priority']
                    and row['target'] < selected[path]['target'])):
            selected[path] = dict(row)
    # Inspect the complete duplicate-resolved set before dropping shadowed rules.
    retained = []
    for path, row in selected.items():
        ancestors = ['/'] if path != '/' else []
        ancestors.extend(path[:index] for index, char in enumerate(path)
                         if char == '/' and index > 0)
        if any(ancestor in selected
               and selected[ancestor]['target'] == row['target']
               and selected[ancestor]['priority'] >= row['priority']
               for ancestor in ancestors):
            continue
        retained.append(row)
    rules = sorted(retained, key=lambda row: (-row['priority'], -len(row['path']), row['path']))
    return {'rules': rules, 'targets': sorted({row['target'] for row in rules})}
