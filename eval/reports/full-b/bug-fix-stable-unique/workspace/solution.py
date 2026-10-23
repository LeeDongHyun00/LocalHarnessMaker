"""Public task implementation."""


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))
