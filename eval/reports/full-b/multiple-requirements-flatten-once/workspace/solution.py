"""Public task implementation."""


def flatten(items: list[list[int]]) -> list[int]:
    """Flatten exactly one list level, preserving all values and their order.

    Ignore empty inner lists. Return a new list without modifying the input
    collection or any inner list.
    """
    return [value for group in items for value in group]
