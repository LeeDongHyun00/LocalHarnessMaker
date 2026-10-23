"""Public task implementation."""


def _pairs(items: list[int]) -> list[tuple[int, int]]:
    return list(zip(items, items[1:]))


def pairs(items: list[int]) -> list[tuple[int, int]]:
    return _pairs(items)


def pairs_legacy(items: list[int]) -> list[tuple[int, int]]:
    return _pairs(items)
