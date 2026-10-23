"""Public task implementation."""


def normalize(text: str) -> str:
    """Convert CRLF and lone CR line endings to LF without other changes."""
    return text.replace("\r\n", "\n").replace("\r", "\n")
