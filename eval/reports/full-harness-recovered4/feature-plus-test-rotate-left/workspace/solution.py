"""Public task implementation."""


def rotate(items: list[int], steps: int) -> list[int]:
    """Return a new list rotated left by steps, or right for negative steps."""
    if not items:
        return []
    offset = steps % len(items)
    return items[offset:] + items[:offset]
