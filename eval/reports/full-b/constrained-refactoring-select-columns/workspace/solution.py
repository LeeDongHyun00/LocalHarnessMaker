"""Public task implementation."""


def _select(rows: list[dict[str, int]], columns: list[str]) -> list[dict[str, int]]:
    return [{key: row[key] for key in columns if key in row} for row in rows]


def select(rows: list[dict[str, int]], columns: list[str]) -> list[dict[str, int]]:
    return _select(rows, columns)


def select_legacy(rows: list[dict[str, int]], columns: list[str]) -> list[dict[str, int]]:
    return _select(rows, columns)
