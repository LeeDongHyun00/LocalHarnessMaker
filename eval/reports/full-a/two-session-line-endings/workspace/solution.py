"""Public task implementation."""


def normalize(text: str) -> str:
    """Convert CRLF and lone CR line endings to LF without stripping text."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def normalize_many(cases: list[tuple]) -> list:
    """Normalize each positional-argument tuple in order, stopping on error."""
    return [normalize(*case) for case in cases]
