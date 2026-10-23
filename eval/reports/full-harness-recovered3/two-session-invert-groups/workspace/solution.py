"""Public task implementation."""


def invert(items: dict[str, str]) -> dict[str, list[str]]:
    """Group keys by value, preserving their input insertion order."""
    grouped: dict[str, list[str]] = {}
    for key, value in items.items():
        grouped.setdefault(value, []).append(key)
    return grouped


def invert_many(cases: list[tuple]) -> list:
    """Call invert with each case's positional arguments, in order.

    Inputs are left unchanged, and the first exception propagates immediately.
    """
    return [invert(*case) for case in cases]
