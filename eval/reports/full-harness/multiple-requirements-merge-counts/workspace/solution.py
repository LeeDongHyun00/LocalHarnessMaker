"""Public task implementation."""


def merge(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    """Return a new dictionary containing the union of both inputs' keys.

    Add counts for shared keys and retain counts for keys in only one input,
    including zero and negative totals. Neither input is changed. Keys appear
    in left's iteration order, followed by right-only keys in right's iteration
    order; shared keys retain their position from left.
    """
    result = left.copy()
    for key, count in right.items():
        result[key] = result.get(key, 0) + count
    return result
