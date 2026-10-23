"""Public task implementation."""


def prefix(items: list[int]) -> list[int]:
    """Return inclusive running sums without modifying items."""
    result: list[int] = []
    total = 0
    for item in items:
        total += item
        result.append(total)
    return result


def prefix_many(cases: list[tuple]) -> list:
    """Call prefix with each case's positional arguments, in order."""
    return [prefix(*case) for case in cases]
