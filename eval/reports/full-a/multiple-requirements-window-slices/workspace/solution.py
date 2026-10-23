"""Public task implementation."""


def windows(items: list[int], size: int) -> list[list[int]]:
    """Return all contiguous windows of exactly ``size``, advancing by one.

    Preserve input values and their order without mutating ``items``. Each
    window is a new list. Return [] when ``size`` exceeds the input length.
    Raise ValueError when ``size`` is zero or negative.
    """
    if size <= 0:
        raise ValueError("size must be positive")
    return [items[i:i + size] for i in range(len(items) - size + 1)]
