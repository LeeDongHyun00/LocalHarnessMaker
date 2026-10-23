"""Public task implementation."""


def flatten(items: list[list[int]]) -> list[int]:
    """Flatten exactly one list level, preserving values and collection order.

    Ignore empty inner lists and return a new list without modifying the
    input outer list or any inner list.
    """
    return [value for group in items for value in group]
