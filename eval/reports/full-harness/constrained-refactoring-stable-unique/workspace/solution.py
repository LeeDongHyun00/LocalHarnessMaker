"""Public task implementation."""


def unique(items: list[str]) -> list[str]:
    return _unique(items)


def unique_legacy(items: list[str]) -> list[str]:
    return _unique(items)


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))
