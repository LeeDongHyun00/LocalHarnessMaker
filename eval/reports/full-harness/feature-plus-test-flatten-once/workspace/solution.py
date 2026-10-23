"""Public task implementation."""


def flatten(items: list[list[int]]) -> list[int]:
    """Return a new list containing each inner list's elements in order."""
    return [item for inner in items for item in inner]
