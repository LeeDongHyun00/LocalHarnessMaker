"""Public task implementation."""


def invert(items: dict[str, str]) -> dict[str, list[str]]:
    """Group input keys by their values without modifying the input.

    Each output list follows the input dictionary's key insertion order.
    Output groups follow the first occurrence of each value, and values are
    preserved unchanged. Empty input returns an empty dictionary.
    """
    result: dict[str, list[str]] = {}
    for key, value in items.items():
        result.setdefault(value, []).append(key)
    return result
