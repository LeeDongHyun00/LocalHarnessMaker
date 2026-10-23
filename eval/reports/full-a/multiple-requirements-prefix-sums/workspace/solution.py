"""Public task implementation."""


def prefix(items: list[int]) -> list[int]:
    """Return inclusive prefix sums in input order without modifying items.

    The result has the same length as items, and each element is the sum of
    all input values up to and including that position. Negative numbers are
    supported, and empty input returns an empty list.
    """
    result: list[int] = []
    total = 0
    for item in items:
        total += item
        result.append(total)
    return result
