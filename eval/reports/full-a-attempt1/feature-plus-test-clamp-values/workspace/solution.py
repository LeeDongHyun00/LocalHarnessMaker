"""Public task implementation."""


def clamp(value: int, low: int, high: int) -> int:
    """Return value limited to the inclusive bounds, rejecting reversed bounds."""
    if low > high:
        raise ValueError("low must be less than or equal to high")
    return min(max(value, low), high)
