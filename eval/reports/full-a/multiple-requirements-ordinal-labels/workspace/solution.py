"""Public task implementation."""


def ordinal(value: int) -> str:
    """Format a nonnegative integer with its English ordinal suffix.

    Use ``st``, ``nd``, and ``rd`` for values ending in 1, 2, and 3,
    respectively, except that values ending in 11, 12, or 13 use ``th``.
    All other values use ``th``, including zero (``0th``).
    Raise ValueError for negative values. The input value is not modified;
    applying this function to a collection does not mutate or reorder it.
    """
    if value < 0:
        raise ValueError("ordinal requires a nonnegative integer")
    suffix = 'th' if 11 <= value % 100 <= 13 else {
        1: 'st', 2: 'nd', 3: 'rd'
    }.get(value % 10, 'th')
    return str(value) + suffix
