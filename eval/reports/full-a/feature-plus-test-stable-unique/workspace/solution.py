"""Public task implementation."""


def unique(items: list[str]) -> list[str]:
    """Return distinct strings in their first-occurrence order."""
    return list(dict.fromkeys(items))
