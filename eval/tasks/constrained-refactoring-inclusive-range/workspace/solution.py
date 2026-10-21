"""Public task implementation."""


def inclusive(start: int, stop: int) -> list[int]:
    step = 1 if stop >= start else -1
    return list(range(start, stop + step, step))


def inclusive_legacy(start: int, stop: int) -> list[int]:
    step = 1 if stop >= start else -1
    return list(range(start, stop + step, step))
