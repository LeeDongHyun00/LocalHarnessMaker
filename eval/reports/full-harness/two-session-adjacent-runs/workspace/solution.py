"""Public task implementation."""


def runs(items: list[str]) -> list[tuple[str, int]]:
    """Encode adjacent equal strings without modifying items."""
    result: list[tuple[str, int]] = []
    for value in items:
        if result and result[-1][0] == value:
            previous, count = result[-1]
            result[-1] = (previous, count + 1)
        else:
            result.append((value, 1))
    return result


def runs_many(cases: list[tuple]) -> list:
    """Return runs results in case order, letting the first exception propagate."""
    return [runs(*case) for case in cases]
