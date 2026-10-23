"""Public task implementation."""


def prefix(items: list[int]) -> list[int]:
    """Return inclusive prefix sums without modifying items."""
    result: list[int] = []
    total = 0
    for item in items:
        total += item
        result.append(total)
    return result


def prefix_many(cases: list[tuple]) -> list:
    """Return prefix results in case order, propagating the first exception."""
    return [prefix(*case) for case in cases]
