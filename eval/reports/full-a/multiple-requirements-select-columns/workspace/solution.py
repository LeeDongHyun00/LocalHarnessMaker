"""Public task implementation."""


def select(rows: list[dict[str, int]], columns: list[str]) -> list[dict[str, int]]:
    """Return a new dictionary of requested columns for each row, in row order.

    Keys follow the requested column order, with repeated names included only
    once and missing keys omitted. Values are preserved without copying or
    conversion. Each result dictionary is new, and neither the rows nor the
    input collections are modified.
    """
    return [{key: row[key] for key in columns if key in row} for row in rows]
