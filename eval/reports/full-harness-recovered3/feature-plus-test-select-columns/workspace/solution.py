"""Public task implementation."""


def select(rows: list[dict[str, int]], columns: list[str]) -> list[dict[str, int]]:
    """Return fresh rows with existing requested keys in column order."""
    return [{column: row[column] for column in columns if column in row} for row in rows]
