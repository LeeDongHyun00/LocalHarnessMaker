"""Public task implementation."""


def _normalize(text: str) -> str:
    return text.replace('\r\n', '\n').replace('\r', '\n')


def normalize(text: str) -> str:
    return _normalize(text)


def normalize_legacy(text: str) -> str:
    return _normalize(text)
