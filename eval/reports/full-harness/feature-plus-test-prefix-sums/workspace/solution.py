"""Public task implementation."""


def prefix(items: list[int]) -> list[int]:
    """Return inclusive prefix sums without modifying items."""
    sums: list[int] = []
    total = 0
    for item in items:
        total += item
        sums.append(total)
    return sums
