"""Public task implementation."""


def last_index(items: list[str], target: str) -> int | None:
    """Return the last zero-based index equal to target, or None if absent.

    Empty input returns None. Matching is case-sensitive. Input values and
    collection order are preserved; the input collection is not mutated.
    """
    for index in range(len(items) - 1, -1, -1):
        if items[index] == target:
            return index
    return None
