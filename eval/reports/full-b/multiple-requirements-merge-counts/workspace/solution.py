"""Public task implementation."""


def merge(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    """Return a new dictionary containing the union of both inputs' keys.

    Add counts for shared keys and retain counts for keys in only one input,
    including zero and negative totals. Preserve the order of keys in left,
    then append keys unique to right in their original order. Neither input's
    values nor key order are changed.
    """
    merged = left.copy()
    for key, count in right.items():
        merged[key] = merged.get(key, 0) + count
    return merged
