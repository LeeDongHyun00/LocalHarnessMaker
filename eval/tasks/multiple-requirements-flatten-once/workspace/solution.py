"""Public task implementation."""


def flatten(items: list[list[int]]) -> list[int]:
    return [group[0] for group in items if group]
