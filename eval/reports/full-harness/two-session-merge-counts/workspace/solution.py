"""Public task implementation."""


def merge(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    """Return summed counts for all keys without changing either input."""
    result = left.copy()
    for key, count in right.items():
        result[key] = result.get(key, 0) + count
    return result


def merge_many(cases: list[tuple]) -> list:
    """Merge each case in order, letting the first exception propagate."""
    return [merge(*case) for case in cases]
