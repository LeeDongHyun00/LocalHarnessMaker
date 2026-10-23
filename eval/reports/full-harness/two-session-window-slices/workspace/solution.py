"""Public task implementation."""


def windows(items: list[int], size: int) -> list[list[int]]:
    """Return each contiguous window of ``size`` without changing ``items``."""
    if size <= 0:
        raise ValueError("size must be positive")
    return [items[start : start + size] for start in range(len(items) - size + 1)]


def windows_many(cases: list[tuple]) -> list:
    """Call ``windows`` for each case in order, stopping at the first exception."""
    return [windows(*case) for case in cases]
