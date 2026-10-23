"""Public task implementation."""


def windows(items: list[int], size: int) -> list[list[int]]:
    """Return contiguous windows of a positive size, advancing by one."""
    if size <= 0:
        raise ValueError("size must be positive")
    return [items[start : start + size] for start in range(len(items) - size + 1)]
