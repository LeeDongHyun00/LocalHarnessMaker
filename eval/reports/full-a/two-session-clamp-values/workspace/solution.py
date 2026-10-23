"""Public task implementation."""


def clamp(value: int, low: int, high: int) -> int:
    """Return value within inclusive bounds, rejecting reversed bounds."""
    if low > high:
        raise ValueError("low must be less than or equal to high")
    return min(max(value, low), high)


def clamp_many(cases: list[tuple]) -> list:
    """Clamp each case in order, propagating the first exception unchanged."""
    return [clamp(*case) for case in cases]
