"""Public task implementation."""


def strip_prefix(text: str, prefix: str) -> str:
    """Remove exactly one matching, nonempty prefix from text."""
    if prefix and text.startswith(prefix):
        return text[len(prefix):]
    return text
