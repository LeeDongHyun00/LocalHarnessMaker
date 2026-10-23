"""Public task implementation."""


def common(items: list[str]) -> str:
    """Return the longest common character prefix of items, case-sensitively.

    Empty input returns an empty string; one item returns that item.
    Input values and collection order are preserved without mutation.
    """
    if not items:
        return ""

    prefix = items[0]
    for item in items[1:]:
        length = 0
        while length < min(len(prefix), len(item)) and prefix[length] == item[length]:
            length += 1
        prefix = prefix[:length]
        if not prefix:
            break
    return prefix
