"""Public task implementation."""


def normalize(text: str) -> str:
    """Replace CRLF and lone CR line breaks with LF.

    Preserve existing LF, all other characters, and the number of line
    breaks, including trailing newlines. The input value is unchanged.
    """
    return text.replace('\r\n', '\n').replace('\r', '\n')
