"""Public task implementation."""


def merge(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    """Return combined counts for all keys without changing either input."""
    result = left.copy()
    for key, count in right.items():
        result[key] = result.get(key, 0) + count
    return result


def merge_many(cases: list[tuple]) -> list:
    """Merge each positional-argument tuple in order, stopping on an error."""
    return [merge(*case) for case in cases]
