"""Public task implementation."""


def _windows(items: list[int], size: int) -> list[list[int]]:
    if size <= 0:
        raise ValueError('positive size required')
    return [items[i:i + size] for i in range(len(items) - size + 1)]


def windows(items: list[int], size: int) -> list[list[int]]:
    return _windows(items, size)


def windows_legacy(items: list[int], size: int) -> list[list[int]]:
    return _windows(items, size)
