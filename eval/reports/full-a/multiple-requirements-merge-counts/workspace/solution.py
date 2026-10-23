"""Public task implementation."""


def merge(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    """Return a new dictionary containing the union of both inputs' keys.

    Add counts for shared keys, retaining zero and negative totals. Preserve
    left's key order, then append keys unique to right in right's key order.
    Neither input dictionary is modified.
    """
    result = left.copy()
    for key, count in right.items():
        result[key] = result.get(key, 0) + count
    return result
