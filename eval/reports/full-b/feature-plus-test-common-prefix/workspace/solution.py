"""Public task implementation."""


def common(items: list[str]) -> str:
    """Return the longest case-sensitive character prefix shared by items."""
    if not items:
        return ""

    prefix = items[0]
    for item in items[1:]:
        while not item.startswith(prefix):
            prefix = prefix[:-1]
        if not prefix:
            return ""
    return prefix
