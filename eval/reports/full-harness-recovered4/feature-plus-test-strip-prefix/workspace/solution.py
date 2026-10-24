"""Public task implementation."""


def strip_prefix(text: str, prefix: str) -> str:
    """Remove exactly one matching prefix, leaving other text unchanged."""
    return text.removeprefix(prefix)
