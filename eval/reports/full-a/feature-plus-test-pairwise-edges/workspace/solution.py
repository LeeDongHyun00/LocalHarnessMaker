"""Public task implementation."""


def pairs(items: list[int]) -> list[tuple[int, int]]:
    """Return overlapping adjacent pairs without modifying items."""
    return list(zip(items, items[1:]))
