"""Public task implementation."""


def windows(items: list[int], size: int) -> list[list[int]]:
    """Return every full window, advancing one item; reject nonpositive sizes."""
    if size <= 0:
        raise ValueError("size must be positive")
    return [items[i:i + size] for i in range(len(items) - size + 1)]
