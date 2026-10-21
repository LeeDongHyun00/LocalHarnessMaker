"""Public task implementation."""


def common(items: list[str]) -> str:
    if not items: return ''
    prefix = items[0]
    for item in items[1:]:
        while not item.startswith(prefix): prefix = prefix[:-1]
    return prefix


def common_legacy(items: list[str]) -> str:
    if not items: return ''
    prefix = items[0]
    for item in items[1:]:
        while not item.startswith(prefix): prefix = prefix[:-1]
    return prefix
