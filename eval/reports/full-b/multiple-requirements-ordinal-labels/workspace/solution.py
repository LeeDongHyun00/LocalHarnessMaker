"""Public task implementation."""


def ordinal(value: int) -> str:
    """Return a nonnegative integer formatted with its English ordinal suffix.

    Values ending in 11, 12, or 13 use "th", including 111, 112, and 113.
    Otherwise, the final digit selects "st" for 1, "nd" for 2, "rd" for 3,
    and "th" for all other digits. Zero is "0th".

    Raise ValueError for negative values. The input value is not modified.
    """
    if value < 0:
        raise ValueError("value must be nonnegative")

    if 11 <= value % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"
