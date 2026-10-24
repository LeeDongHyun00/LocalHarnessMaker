"""Public task implementation."""


def clamp(value: int, low: int, high: int) -> int:
    """Return value within the inclusive bounds, rejecting reversed bounds."""
    if low > high:
        raise ValueError("low must be less than or equal to high")
    if value < low:
        return low
    if value > high:
        return high
    return value


def clamp_many(cases: list[tuple]) -> list:
    """Clamp cases in order without mutation; propagate the first exception."""
    return [clamp(*case) for case in cases]
