"""Public task implementation."""


def normalize(text: str) -> str:
    return text.replace('\r\n', '\n').replace('\r', '\n')
