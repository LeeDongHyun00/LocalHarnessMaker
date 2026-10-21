"""Public task implementation."""


def runs(items: list[str]) -> list[tuple[str, int]]:
    return [(value, items.count(value)) for value in dict.fromkeys(items)]
