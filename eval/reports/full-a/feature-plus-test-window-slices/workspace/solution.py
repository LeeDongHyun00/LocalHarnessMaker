"""Public task implementation."""


def windows(items: list[int], size: int) -> list[list[int]]:
    """Return each contiguous window of size elements without modifying items."""
    if size <= 0:
        raise ValueError("size must be positive")
    return [items[start : start + size] for start in range(len(items) - size + 1)]
