"""Public task implementation."""


def inclusive(start: int, stop: int) -> list[int]:
    """Return all integers from start through stop, including both endpoints.

    Step by +1 when start < stop and by -1 when start > stop. Equal
    endpoints produce a singleton list. Preserve traversal order and leave
    input values and collections unchanged.
    """
    step = 1 if start <= stop else -1
    return list(range(start, stop + step, step))
