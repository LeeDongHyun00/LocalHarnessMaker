"""Public task implementation."""


def windows(items: list[int], size: int) -> list[list[int]]:
    """Return every contiguous window of size, without modifying items."""
    if size <= 0:
        raise ValueError("size must be positive")
    return [items[start : start + size] for start in range(len(items) - size + 1)]


def windows_many(cases: list[tuple]) -> list:
    """Call windows with each case's positional arguments, in order."""
    return [windows(*case) for case in cases]
