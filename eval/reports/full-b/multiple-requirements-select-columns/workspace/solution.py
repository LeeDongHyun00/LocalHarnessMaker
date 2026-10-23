"""Public task implementation."""


def select(rows: list[dict[str, int]], columns: list[str]) -> list[dict[str, int]]:
    """Return a new dictionary of requested columns for every input row.

    Preserve row order and order each result by the first occurrence of each
    requested column. Omit missing keys and include repeated column names only
    once. Preserve values without copying them, and do not modify the rows or
    either input collection.
    """
    return [{key: row[key] for key in columns if key in row} for row in rows]
