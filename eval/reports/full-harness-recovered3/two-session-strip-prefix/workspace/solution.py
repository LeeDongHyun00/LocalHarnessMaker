"""Public task implementation."""


def strip_prefix(text: str, prefix: str) -> str:
    """Remove exactly one matching prefix, leaving other text unchanged."""
    return text.removeprefix(prefix)


def strip_prefix_many(cases: list[tuple]) -> list:
    """Call strip_prefix for each argument tuple, stopping at the first error."""
    return [strip_prefix(*args) for args in cases]
