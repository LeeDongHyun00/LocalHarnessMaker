"""Public task implementation."""


def inclusive(start: int, stop: int) -> list[int]:
    """Return all integers from start through stop, including both endpoints.

    Step by +1 when start < stop and by -1 when start > stop. Equal
    endpoints return a singleton list. Preserve the input values and return
    the integers in traversal order from start to stop.
    """
    step = 1 if start <= stop else -1
    return list(range(start, stop + step, step))
