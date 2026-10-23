"""Public task implementation."""


def normalize(text: str) -> str:
    """Replace each CRLF pair and lone CR with LF.

    Preserve existing LF, all other characters, and the number of line
    breaks, including trailing newlines. The input string is unchanged.
    """
    return text.replace('\r\n', '\n').replace('\r', '\n')
