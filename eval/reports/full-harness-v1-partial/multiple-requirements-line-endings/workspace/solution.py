"""Public task implementation."""


def normalize(text: str) -> str:
    """Replace CRLF and lone CR line breaks with LF.

    Preserve existing LF, all other characters, and the number of line
    breaks (each CRLF pair counts as one). Do not strip trailing newlines.
    The input string is unchanged.
    """
    return text.replace('\r\n', '\n').replace('\r', '\n')
