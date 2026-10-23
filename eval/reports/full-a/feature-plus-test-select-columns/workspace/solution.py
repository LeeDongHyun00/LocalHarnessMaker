"""Public task implementation."""


def select(rows: list[dict[str, int]], columns: list[str]) -> list[dict[str, int]]:
    """Return new row dictionaries with the requested, available columns."""
    unique_columns = list(dict.fromkeys(columns))
    return [
        {column: row[column] for column in unique_columns if column in row}
        for row in rows
    ]
