"""Public task implementation."""


def pairs(items: list[int]) -> list[tuple[int, int]]:
    """Return overlapping adjacent pairs in input order without changing items.

    Inputs with fewer than two items return an empty list. For example,
    [1, 2, 3] returns [(1, 2), (2, 3)]. Input values are preserved.
    """
    return list(zip(items, items[1:]))
