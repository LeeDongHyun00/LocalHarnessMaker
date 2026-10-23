"""Public task implementation."""


def _invert(items: dict[str, str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for key, value in items.items():
        result.setdefault(value, []).append(key)
    return result


def invert(items: dict[str, str]) -> dict[str, list[str]]:
    return _invert(items)


def invert_legacy(items: dict[str, str]) -> dict[str, list[str]]:
    return _invert(items)
