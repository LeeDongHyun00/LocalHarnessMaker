"""Public task implementation."""


def prefix(items: list[int]) -> list[int]:
    """Return inclusive running sums without modifying items."""
    result: list[int] = []
    total = 0
    for item in items:
        total += item
        result.append(total)
    return result
