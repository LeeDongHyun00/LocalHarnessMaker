"""Public task implementation."""


def invert(items: dict[str, str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for key, value in items.items(): result.setdefault(value, []).append(key)
    return result


def invert_legacy(items: dict[str, str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for key, value in items.items(): result.setdefault(value, []).append(key)
    return result
