"""Public task implementation."""


def clamp(value: int, low: int, high: int) -> int:
    """Clamp value into the inclusive [low, high] range.

    Return low when value is below low, high when value is above high,
    and value unchanged otherwise. Equal bounds are valid.
    Raise ValueError if low > high.
    """
    if low > high:
        raise ValueError("low must be less than or equal to high")
    if value < low:
        return low
    if value > high:
        return high
    return value
