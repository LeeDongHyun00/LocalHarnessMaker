"""Public task implementation."""


def clamp(value: int, low: int, high: int) -> int:
    """Return value constrained to the inclusive bounds.

    Raise ValueError if low is greater than high.
    """
    if low > high:
        raise ValueError("low must be less than or equal to high")
    return min(max(value, low), high)
