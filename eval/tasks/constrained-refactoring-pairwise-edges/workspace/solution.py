"""Public task implementation."""


def pairs(items: list[int]) -> list[tuple[int, int]]:
    return list(zip(items, items[1:]))


def pairs_legacy(items: list[int]) -> list[tuple[int, int]]:
    return list(zip(items, items[1:]))
