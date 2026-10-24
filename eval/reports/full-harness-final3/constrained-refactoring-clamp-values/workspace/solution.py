"""Public task implementation."""


def _clamp(value: int, low: int, high: int) -> int:
    if low > high:
        raise ValueError('reversed bounds')
    return max(low, min(value, high))


def clamp(value: int, low: int, high: int) -> int:
    return _clamp(value, low, high)


def clamp_legacy(value: int, low: int, high: int) -> int:
    return _clamp(value, low, high)
