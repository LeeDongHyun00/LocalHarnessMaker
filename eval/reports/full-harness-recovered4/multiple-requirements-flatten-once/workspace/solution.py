"""Public task implementation."""


def flatten(items: list[list[int]]) -> list[int]:
    """Flatten exactly one list level, preserving outer and inner order.

    Ignore empty inner lists and return a new list without modifying the
    input collection or any inner lists.
    """
    return [value for group in items for value in group]
