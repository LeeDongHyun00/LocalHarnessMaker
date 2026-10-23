"""Public task implementation."""


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def unique(items: list[str]) -> list[str]:
    return _unique(items)


def unique_legacy(items: list[str]) -> list[str]:
    return _unique(items)
