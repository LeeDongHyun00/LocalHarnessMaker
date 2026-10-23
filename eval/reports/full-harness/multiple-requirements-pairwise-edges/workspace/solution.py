"""Public task implementation."""


def pairs(items: list[int]) -> list[tuple[int, int]]:
    """Return overlapping adjacent pairs in input order.

    Inputs with fewer than two items return an empty list. Preserve input
    values and collection order without mutating the input collection.
    For example, [1, 2, 3] returns [(1, 2), (2, 3)].
    """
    return list(zip(items, items[1:]))
