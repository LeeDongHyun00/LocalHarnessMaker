"""Public task implementation."""


def ordinal(value: int) -> str:
    """Format a nonnegative integer as an English ordinal."""
    if value < 0:
        raise ValueError("value must be nonnegative")

    if 11 <= value % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"
