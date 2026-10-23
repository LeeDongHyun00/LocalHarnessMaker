"""Public task implementation."""


def flatten(items: list[list[int]]) -> list[int]:
    """Return the elements of each inner list in order in a new list."""
    return [element for inner in items for element in inner]
