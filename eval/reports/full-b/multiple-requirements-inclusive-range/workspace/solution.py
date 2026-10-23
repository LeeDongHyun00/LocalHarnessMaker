"""Public task implementation."""


def inclusive(start: int, stop: int) -> list[int]:
    """Return all integers from start through stop, including both endpoints.

    Step by +1 when start is less than stop, or by -1 when start is greater
    than stop. Equal endpoints return a singleton list. Input values are
    unchanged, and the returned list is ordered from start to stop.
    """
    step = 1 if start <= stop else -1
    return list(range(start, stop + step, step))
