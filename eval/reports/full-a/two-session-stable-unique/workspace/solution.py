"""Public task implementation."""


def unique(items: list[str]) -> list[str]:
    """Return distinct strings in first-occurrence order without changing items."""
    return list(dict.fromkeys(items))


def unique_many(cases: list[tuple]) -> list:
    """Call unique with each case's positional arguments, in case order.

    Leave inputs unchanged and let the first exception propagate immediately.
    """
    return [unique(*case) for case in cases]
