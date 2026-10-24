"""Public task implementation."""


def pairs(items: list[int]) -> list[tuple[int, int]]:
    """Return overlapping adjacent pairs in input order without changing items."""
    return [(items[index], items[index + 1]) for index in range(len(items) - 1)]


def pairs_many(cases: list[tuple]) -> list:
    """Call pairs with each case's positional arguments, preserving case order."""
    return [pairs(*case) for case in cases]
