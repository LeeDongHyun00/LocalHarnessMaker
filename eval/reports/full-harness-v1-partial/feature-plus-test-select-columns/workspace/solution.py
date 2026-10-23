"""Public task implementation."""


def select(rows: list[dict[str, int]], columns: list[str]) -> list[dict[str, int]]:
    """Return fresh rows with available columns in their requested order."""
    unique_columns = dict.fromkeys(columns)
    return [
        {column: row[column] for column in unique_columns if column in row}
        for row in rows
    ]
