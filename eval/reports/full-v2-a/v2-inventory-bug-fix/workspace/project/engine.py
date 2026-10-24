from .validation import validate

def compute(rows: list[dict]) -> dict:
    rows = validate(rows)
    counts: dict[tuple[str, str], int] = {}
    for row in rows:
        key = (row['sku'], row['location'])
        counts[key] = counts.get(key, 0) + row['delta']
    if any(value < 0 for value in counts.values()):
        raise ValueError('inventory: negative stock')
    stock = [{'sku': key[0], 'location': key[1], 'quantity': value} for key, value in sorted(counts.items())]
    totals: dict[str, int] = {}
    for row in stock:
        totals[row['sku']] = totals.get(row['sku'], 0) + row['quantity']
    return {'stock': stock, 'totals': dict(sorted(totals.items()))}
