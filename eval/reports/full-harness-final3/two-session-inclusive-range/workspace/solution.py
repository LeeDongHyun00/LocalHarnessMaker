"""Public task implementation."""


def inclusive(start: int, stop: int) -> list[int]:
    """Return every integer from start through stop in endpoint order."""
    step = 1 if start <= stop else -1
    return list(range(start, stop + step, step))


def inclusive_many(cases: list[tuple]) -> list:
    """Call inclusive for each case in order, stopping at the first exception."""
    return [inclusive(*case) for case in cases]
