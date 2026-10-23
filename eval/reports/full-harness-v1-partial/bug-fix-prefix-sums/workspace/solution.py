"""Public task implementation."""


def prefix(items: list[int]) -> list[int]:
    return [sum(items[:i + 1]) for i in range(len(items))]
