"""Public task implementation."""


def _runs(items: list[str]) -> list[tuple[str, int]]:
    result: list[tuple[str, int]] = []
    for item in items:
        if result and result[-1][0] == item:
            result[-1] = (item, result[-1][1] + 1)
        else:
            result.append((item, 1))
    return result


def runs(items: list[str]) -> list[tuple[str, int]]:
    return _runs(items)


def runs_legacy(items: list[str]) -> list[tuple[str, int]]:
    return _runs(items)
