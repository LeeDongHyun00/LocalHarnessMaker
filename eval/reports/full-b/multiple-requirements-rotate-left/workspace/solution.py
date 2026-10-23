"""Public task implementation."""


def rotate(items: list[int], steps: int) -> list[int]:
    """Return a new list rotated left by steps modulo the input length.

    Negative steps rotate right. Empty input returns []. Input values and
    their circular order are preserved, and the input list is never mutated.
    For example, rotate([1, 2, 3], 4) returns [2, 3, 1].
    """
    if not items:
        return []
    steps %= len(items)
    return items[steps:] + items[:steps]
