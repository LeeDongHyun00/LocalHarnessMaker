"""Public task implementation."""


def ordinal(value: int) -> str:
    """Format a nonnegative integer with its English ordinal suffix.

    Final digits 1, 2, and 3 use 'st', 'nd', and 'rd'; all others use
    'th'. Values ending in 11, 12, or 13 always use 'th', including
    111, 112, and 113. Zero is '0th'. Negative values raise ValueError.
    The input value is preserved.
    """
    if value < 0:
        raise ValueError('ordinal requires a nonnegative integer')
    suffix = 'th' if 11 <= value % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')
    return str(value) + suffix
