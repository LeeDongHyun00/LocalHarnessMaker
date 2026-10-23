"""Public task implementation."""


def pairs(items: list[int]) -> list[tuple[int, int]]:
    """Return overlapping adjacent pairs without modifying items."""
    return list(zip(items, items[1:]))


def pairs_many(cases: list[tuple]) -> list:
    """Call pairs with each case's positional arguments, in order."""
    return [pairs(*case) for case in cases]
