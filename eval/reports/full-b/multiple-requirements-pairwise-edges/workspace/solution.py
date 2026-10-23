"""Public task implementation."""


def pairs(items: list[int]) -> list[tuple[int, int]]:
    """Return overlapping adjacent pairs in input order.

    Inputs with fewer than two items return []. The input list is not
    mutated or reordered, and its values are preserved.

    >>> pairs([1, 2, 3])
    [(1, 2), (2, 3)]
    """
    return list(zip(items, items[1:]))
