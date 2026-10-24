"""Public task implementation."""


def select(rows: list[dict[str, int]], columns: list[str]) -> list[dict[str, int]]:
    """Return a new dictionary for each row, preserving row order and values.

    Include requested columns in their first-occurrence order, omitting keys
    missing from each row. Repeated column names appear only once. Neither
    the input rows nor the input collections are modified; values are retained
    without copying or conversion.
    """
    return [{key: row[key] for key in columns if key in row} for row in rows]
