"""Public task implementation."""


def prefix(items: list[int]) -> list[int]:
    return [sum(items[:i]) for i in range(len(items))]
