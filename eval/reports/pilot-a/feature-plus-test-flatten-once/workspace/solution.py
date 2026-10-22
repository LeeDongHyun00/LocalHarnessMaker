"""Public task implementation."""


def flatten(items: list[list[int]]) -> list[int]:
    """Return the elements of each inner list in their original order."""
    return [item for inner in items for item in inner]
