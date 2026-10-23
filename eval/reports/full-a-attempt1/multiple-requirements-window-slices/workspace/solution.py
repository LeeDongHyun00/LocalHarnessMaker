"""Public task implementation."""


def windows(items: list[int], size: int) -> list[list[int]]:
    """Return all contiguous windows of exactly ``size``, advancing by one.

    Preserve input values and their order without mutating ``items``.
    Raise ValueError if ``size <= 0``. Return [] if ``size`` exceeds
    the input length.
    """
    if size <= 0:
        raise ValueError("size must be positive")
    return [items[i:i + size] for i in range(len(items) - size + 1)]
