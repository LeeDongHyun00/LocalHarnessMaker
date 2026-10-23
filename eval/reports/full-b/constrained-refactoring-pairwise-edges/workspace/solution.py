"""Public task implementation."""


def _adjacent_pairs(items: list[int]) -> list[tuple[int, int]]:
    return list(zip(items, items[1:]))


def pairs(items: list[int]) -> list[tuple[int, int]]:
    return _adjacent_pairs(items)


def pairs_legacy(items: list[int]) -> list[tuple[int, int]]:
    return _adjacent_pairs(items)
