"""Public task implementation."""


def prefix(items: list[int]) -> list[int]:
    result: list[int] = []
    value = 0
    for item in items:
        value += item
        result.append(value)
    return result


def prefix_legacy(items: list[int]) -> list[int]:
    result: list[int] = []
    value = 0
    for item in items:
        value += item
        result.append(value)
    return result
