"""Public task implementation."""


def pairs(items: list[int]) -> list[tuple[int, int]]:
    return list(zip(items[::2], items[1::2]))
