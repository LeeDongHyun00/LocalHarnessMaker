"""Public task implementation."""


def merge(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    """Return all keys with their counts added, without changing either input."""
    result = left.copy()
    for key, count in right.items():
        result[key] = result.get(key, 0) + count
    return result


def merge_many(cases: list[tuple]) -> list:
    """Merge each case in order, stopping at the first exception."""
    return [merge(*case) for case in cases]
