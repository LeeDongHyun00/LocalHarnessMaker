"""Public task implementation."""


def last_index(items: list[str], target: str) -> int | None:
    """Return the last zero-based index of a value equal to target.

    Matching is case-sensitive. Return None if target is absent or items is
    empty. Preserve all input values and their collection order.
    """
    result: int | None = None
    for index, item in enumerate(items):
        if item == target:
            result = index
    return result
