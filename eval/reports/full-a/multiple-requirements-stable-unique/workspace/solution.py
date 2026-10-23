"""Public task implementation."""


def unique(items: list[str]) -> list[str]:
    """Return each string once, in first-occurrence order.

    Equality is case-sensitive. Empty input returns an empty list.
    The input collection, its order, and its string values are not modified.
    """
    return list(dict.fromkeys(items))
