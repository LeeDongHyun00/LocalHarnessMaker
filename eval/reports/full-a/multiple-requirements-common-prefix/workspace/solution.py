"""Public task implementation."""


def common(items: list[str]) -> str:
    """Return the longest common character prefix of items.

    Matching is case-sensitive. Empty input returns an empty string, and
    a single item returns that item. Input values and collection order
    are preserved; the input collection is not mutated.
    """
    if not items:
        return ""

    prefix = items[0]
    for item in items[1:]:
        length = 0
        for left, right in zip(prefix, item):
            if left != right:
                break
            length += 1
        prefix = prefix[:length]
        if not prefix:
            break
    return prefix
