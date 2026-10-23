"""Public task implementation."""


def unique(items: list[str]) -> list[str]:
    """Return distinct strings in first-occurrence order without changing items."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
