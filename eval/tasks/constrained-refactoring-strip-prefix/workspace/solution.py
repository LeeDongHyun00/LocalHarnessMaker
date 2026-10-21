"""Public task implementation."""


def strip_prefix(text: str, prefix: str) -> str:
    return text[len(prefix):] if prefix and text.startswith(prefix) else text


def strip_prefix_legacy(text: str, prefix: str) -> str:
    return text[len(prefix):] if prefix and text.startswith(prefix) else text
