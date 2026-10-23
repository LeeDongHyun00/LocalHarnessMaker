"""Public task implementation."""


def clamp(value: int, low: int, high: int) -> int:
    if low > high:
        raise ValueError("low must be less than or equal to high")
    return max(low, min(value, high))
