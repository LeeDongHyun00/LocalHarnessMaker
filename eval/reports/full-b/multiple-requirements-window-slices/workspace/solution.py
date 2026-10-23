"""Public task implementation."""


def windows(items: list[int], size: int) -> list[list[int]]:
    """Return all contiguous windows of exactly ``size``, advancing by one.

    Preserve input values, element order, and window order without modifying
    ``items``. Return an empty list if ``size`` exceeds the input length.

    Raises:
        ValueError: If ``size`` is less than or equal to zero.
    """
    if size <= 0:
        raise ValueError("size must be positive")
    return [items[i:i + size] for i in range(len(items) - size + 1)]
