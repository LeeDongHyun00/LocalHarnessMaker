"""Public task implementation."""


def clamp(value: int, low: int, high: int) -> int:
    """Return value clamped to the inclusive [low, high] range.

    Raise ValueError if low > high. Equal bounds are valid. Return value
    unchanged when it is within the range; otherwise return the nearest bound.
    Inputs are not mutated, and collection order is preserved.
    """
    if low > high:
        raise ValueError("low must be less than or equal to high")
    if value < low:
        return low
    if value > high:
        return high
    return value
