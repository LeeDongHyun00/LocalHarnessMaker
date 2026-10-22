"""Public task implementation."""


def clamp(value: int, low: int, high: int) -> int:
    """Return value constrained to the inclusive range, rejecting reversed bounds."""
    if low > high:
        raise ValueError("low must be less than or equal to high")
    if value < low:
        return low
    if value > high:
        return high
    return value
