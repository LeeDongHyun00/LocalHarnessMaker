"""Public task implementation."""


def last_index(items: list[str], target: str) -> int | None:
    """Return the last index equal to target, or None if it is absent."""
    result: int | None = None
    for index, item in enumerate(items):
        if item == target:
            result = index
    return result


def last_index_many(cases: list[tuple]) -> list:
    """Call last_index for each argument tuple, stopping at the first exception."""
    return [last_index(*case) for case in cases]
