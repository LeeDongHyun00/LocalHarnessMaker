"""Public task implementation."""


def rotate(items: list[int], steps: int) -> list[int]:
    return _rotate(items, steps)


def rotate_legacy(items: list[int], steps: int) -> list[int]:
    return _rotate(items, steps)


def _rotate(items: list[int], steps: int) -> list[int]:
    if not items:
        return []
    steps %= len(items)
    return items[steps:] + items[:steps]
