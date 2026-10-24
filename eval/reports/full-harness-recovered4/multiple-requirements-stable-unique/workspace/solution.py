"""Public task implementation."""


def unique(items: list[str]) -> list[str]:
    """Return each string once, preserving its value and first-occurrence order.

    Empty input returns []. Equality is case-sensitive, and the input
    collection is not mutated.
    """
    return list(dict.fromkeys(items))
