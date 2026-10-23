"""Public task implementation."""


def clamp(value: int, low: int, high: int) -> int:
    """Clamp value to the inclusive bounds, rejecting reversed bounds."""
    if low > high:
        raise ValueError("low must be less than or equal to high")
    return min(high, max(low, value))
