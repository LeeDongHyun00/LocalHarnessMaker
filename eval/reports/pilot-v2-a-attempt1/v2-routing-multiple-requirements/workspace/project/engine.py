from .validation import validate

def compute(rows: list[dict]) -> dict:
    rows = validate(rows)
    selected: dict[str, dict] = {}
    for row in rows:
        path = row['path']
        previous = selected.get(path)
        if (previous is None or row['priority'] > previous['priority']
                or (row['priority'] == previous['priority']
                    and row['target'] < previous['target'])):
            selected[path] = dict(row)
    retained = []
    for path, row in selected.items():
        # Consult the complete duplicate-resolved set, including rules that
        # may themselves be shadowed. Prefixes end only at segment boundaries.
        ancestors = [] if path == '/' else ['/']
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
