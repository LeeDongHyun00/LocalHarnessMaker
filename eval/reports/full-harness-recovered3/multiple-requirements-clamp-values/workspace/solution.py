"""Public task implementation."""


def clamp(value: int, low: int, high: int) -> int:
    """Clamp value into the inclusive [low, high] range.

    Return low if value is below low, high if value is above high,
    and value otherwise. Equal bounds are valid. Raise ValueError if
    low > high. Inputs are not mutated.
    """
    if low > high:
        raise ValueError("low must be less than or equal to high")
    return max(low, min(value, high))
