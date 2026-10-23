"""Public task implementation."""


def unique(items: list[str]) -> list[str]:
    """Return each string once, in first-occurrence order.

    Equality is case-sensitive, and empty input returns an empty list.
    Input collections and their string values are left unchanged.
    """
    return list(dict.fromkeys(items))
