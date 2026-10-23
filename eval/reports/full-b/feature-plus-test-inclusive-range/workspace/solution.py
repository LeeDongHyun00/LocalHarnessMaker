"""Public task implementation."""


def inclusive(start: int, stop: int) -> list[int]:
    """Return consecutive integers from start through stop, including both."""
    step = 1 if start <= stop else -1
    return list(range(start, stop + step, step))
