"""Public task implementation."""


def normalize(text: str) -> str:
    """Return text with CRLF and lone CR line breaks replaced by LF.

    Preserve existing LF, all other characters, and the number of line
    breaks, including trailing newlines. The input is not modified.
    """
    return text.replace('\r\n', '\n').replace('\r', '\n')
