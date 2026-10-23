"""Public task implementation."""


def unique(items: list[str]) -> list[str]:
    """Return each string once, in first-occurrence order.

    Equality is case-sensitive. Empty input returns an empty list.
    Input values and the input collection's order are preserved; the input
    collection is not mutated.
    """
    return list(dict.fromkeys(items))
