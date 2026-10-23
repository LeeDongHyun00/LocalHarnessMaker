"""Public task implementation."""


def last_index(items: list[str], target: str) -> int | None:
    """Return the last index equal to target, or None if no item matches."""
    for index in range(len(items) - 1, -1, -1):
        if items[index] == target:
            return index
    return None


def last_index_many(cases: list[tuple]) -> list:
    """Call last_index with each case's positional arguments, in order.

    Stop at the first exception and let it propagate unchanged.
    """
    return [last_index(*case) for case in cases]
