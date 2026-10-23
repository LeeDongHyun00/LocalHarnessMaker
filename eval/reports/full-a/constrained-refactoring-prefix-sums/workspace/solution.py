"""Public task implementation."""


def _prefix(items: list[int]) -> list[int]:
    result: list[int] = []
    value = 0
    for item in items:
        value += item
        result.append(value)
    return result


def prefix(items: list[int]) -> list[int]:
    return _prefix(items)


def prefix_legacy(items: list[int]) -> list[int]:
    return _prefix(items)
