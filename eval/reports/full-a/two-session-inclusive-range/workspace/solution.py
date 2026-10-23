"""Public task implementation."""


def inclusive(start: int, stop: int) -> list[int]:
    """Return integers from start through stop, including both endpoints."""
    step = 1 if start <= stop else -1
    return list(range(start, stop + step, step))


def inclusive_many(cases: list[tuple]) -> list:
    """Call inclusive with each case in order, propagating the first error."""
    return [inclusive(*case) for case in cases]
