"""Public task implementation."""


def common(items: list[str]) -> str:
    """Return the longest case-sensitive character prefix shared by items."""
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
