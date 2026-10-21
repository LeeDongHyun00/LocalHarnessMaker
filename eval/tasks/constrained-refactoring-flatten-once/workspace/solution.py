"""Public task implementation."""


def flatten(items: list[list[int]]) -> list[int]:
    return [item for group in items for item in group]


def flatten_legacy(items: list[list[int]]) -> list[int]:
    return [item for group in items for item in group]
