from .validation import validate

def compute(rows: list[dict]) -> dict:
    rows = validate(rows)
    seen: set[str] = set()
    bookings: list[dict] = []
    for row in rows:
        if row['id'] in seen:
            raise ValueError('reservations: duplicate id')
        seen.add(row['id'])
        for old in bookings:
            if old['resource'] == row['resource'] and old['start'] < row['end'] and row['start'] < old['end']:
                raise ValueError('reservations: conflict')
        bookings.append(dict(row))
    bookings.sort(key=lambda row: (row['resource'], row['start'], row['end'], row['id']))
    return {'bookings': bookings, 'resources': sorted({row['resource'] for row in bookings})}
