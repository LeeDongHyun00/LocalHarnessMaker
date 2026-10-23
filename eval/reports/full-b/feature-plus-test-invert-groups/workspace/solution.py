"""Public task implementation."""


def invert(items: dict[str, str]) -> dict[str, list[str]]:
    """Group keys by value, preserving their insertion order in each group."""
    grouped: dict[str, list[str]] = {}
    for key, value in items.items():
        grouped.setdefault(value, []).append(key)
    return grouped
