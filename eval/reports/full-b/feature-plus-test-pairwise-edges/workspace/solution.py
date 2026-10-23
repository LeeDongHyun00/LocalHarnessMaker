"""Public task implementation."""


def pairs(items: list[int]) -> list[tuple[int, int]]:
    """Return overlapping adjacent pairs in input order."""
    return list(zip(items, items[1:]))
