"""Public task implementation."""


def _inclusive(start: int, stop: int) -> list[int]:
    step = 1 if stop >= start else -1
    return list(range(start, stop + step, step))


def inclusive(start: int, stop: int) -> list[int]:
    return _inclusive(start, stop)


def inclusive_legacy(start: int, stop: int) -> list[int]:
    return _inclusive(start, stop)
