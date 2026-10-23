"""Public task implementation."""


def strip_prefix(text: str, prefix: str) -> str:
    """Remove exactly one matching prefix from text.

    A nonmatching or empty prefix leaves text unchanged. The prefix is
    matched as a whole string, not as individual characters, and repeated
    prefixes are not removed. Input values are not modified.
    """
    return text.removeprefix(prefix)
