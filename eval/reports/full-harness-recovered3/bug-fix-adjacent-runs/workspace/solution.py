"""Public task implementation."""


def runs(items: list[str]) -> list[tuple[str, int]]:
    result: list[tuple[str, int]] = []
    for value in items:
        if result and result[-1][0] == value:
            result[-1] = (value, result[-1][1] + 1)
        else:
            result.append((value, 1))
    return result
