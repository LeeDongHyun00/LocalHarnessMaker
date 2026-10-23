"""Public task implementation."""


def strip_prefix(text: str, prefix: str) -> str:
    """Remove exactly one leading occurrence of prefix, if present."""
    return text.removeprefix(prefix)


def strip_prefix_many(cases: list[tuple]) -> list:
    """Call strip_prefix with each case's arguments, stopping on any exception."""
    return [strip_prefix(*case) for case in cases]
