"""Public task implementation."""


def invert(items: dict[str, str]) -> dict[str, list[str]]:
    """Group keys by value, preserving their insertion order in each group."""
    grouped: dict[str, list[str]] = {}
    for key, value in items.items():
        grouped.setdefault(value, []).append(key)
    return grouped


def invert_many(cases: list[tuple]) -> list:
    """Call invert with each case's positional arguments, in case order.

    Stop at the first exception and let it propagate unchanged.
    """
    return [invert(*case) for case in cases]
