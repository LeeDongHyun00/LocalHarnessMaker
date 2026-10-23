"""Public task implementation."""


def rotate(items: list[int], steps: int) -> list[int]:
    """Return a new list rotated left by steps (right for negative steps)."""
    if not items:
        return []
    offset = steps % len(items)
    return items[offset:] + items[:offset]


def rotate_many(cases: list[tuple]) -> list:
    """Call rotate with each case's positional arguments, in order."""
    return [rotate(*case) for case in cases]
