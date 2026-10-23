"""Public task implementation."""


def pairs(items: list[int]) -> list[tuple[int, int]]:
    return _adjacent_pairs(items)


def pairs_legacy(items: list[int]) -> list[tuple[int, int]]:
    return _adjacent_pairs(items)


def _adjacent_pairs(items: list[int]) -> list[tuple[int, int]]:
    """Build adjacent pairs without mutating items, preserving slicing errors."""
    return list(zip(items, items[1:]))
