"""Public task implementation."""


def select(rows: list[dict[str, int]], columns: list[str]) -> list[dict[str, int]]:
    return [{key: row[key] for key in columns} for row in rows]
