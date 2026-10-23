"""Public task implementation."""


def flatten(items: list[list[int]]) -> list[int]:
    """Return the elements of each inner list in order, without mutation."""
    return [item for inner in items for item in inner]


def flatten_many(cases: list[tuple]) -> list:
    """Call flatten with each case's positional arguments, stopping on error."""
    return [flatten(*case) for case in cases]
