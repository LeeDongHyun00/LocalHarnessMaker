"""Public task implementation."""


def inclusive(start: int, stop: int) -> list[int]:
    """Return integers from start through stop, including both endpoints.

    Step by +1 when start is less than stop and by -1 when start is
    greater than stop. Equal endpoints produce a singleton list.
    Input values are preserved, and the result follows traversal order.
    """
    step = 1 if start <= stop else -1
    return list(range(start, stop + step, step))
