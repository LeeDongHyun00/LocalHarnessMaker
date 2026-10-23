"""Public task implementation."""


def rotate(items: list[int], steps: int) -> list[int]:
    """Return a new list rotated left by steps modulo the input length.

    Negative steps rotate right, and empty input returns []. For example,
    rotate([1, 2, 3], 4) returns [2, 3, 1]. Input values and their cyclic
    order are preserved, and the input collection is never mutated.
    """
    if not items:
        return []
    steps %= len(items)
    return items[steps:] + items[:steps]
