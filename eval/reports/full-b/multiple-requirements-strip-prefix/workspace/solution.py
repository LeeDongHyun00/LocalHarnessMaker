"""Public task implementation."""


def strip_prefix(text: str, prefix: str) -> str:
    """Remove exactly one matching prefix from the start of text.

    An empty or nonmatching prefix leaves text unchanged. Match prefix as
    a whole string, never as individual characters, and leave any further
    occurrences in place. Neither input value is modified.
    """
    return text.removeprefix(prefix)
