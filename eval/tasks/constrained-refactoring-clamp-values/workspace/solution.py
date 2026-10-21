"""Public task implementation."""


def clamp(value: int, low: int, high: int) -> int:
    if low > high: raise ValueError('reversed bounds')
    return max(low, min(value, high))


def clamp_legacy(value: int, low: int, high: int) -> int:
    if low > high: raise ValueError('reversed bounds')
    return max(low, min(value, high))
