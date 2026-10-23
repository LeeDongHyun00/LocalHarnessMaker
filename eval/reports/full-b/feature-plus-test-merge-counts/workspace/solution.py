"""Public task implementation."""


def merge(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    """Combine counts for all keys without changing either input."""
    result = left.copy()
    for key, count in right.items():
        result[key] = result.get(key, 0) + count
    return result
