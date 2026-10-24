"""Public task implementation."""


def inclusive(start: int, stop: int) -> list[int]:
    step = 1 if start <= stop else -1
    return list(range(start, stop + step, step))
