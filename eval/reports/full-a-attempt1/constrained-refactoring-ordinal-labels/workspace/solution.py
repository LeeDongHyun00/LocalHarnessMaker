"""Public task implementation."""


def _ordinal(value: int) -> str:
    if value < 0: raise ValueError('nonnegative value required')
    suffix = 'th' if 10 <= value % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')
    return str(value) + suffix


def ordinal(value: int) -> str:
    return _ordinal(value)


def ordinal_legacy(value: int) -> str:
    return _ordinal(value)
