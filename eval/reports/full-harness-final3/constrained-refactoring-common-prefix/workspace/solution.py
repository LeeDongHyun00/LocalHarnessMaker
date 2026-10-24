"""Public task implementation."""


def _common_prefix(items: list[str]) -> str:
    if not items:
        return ''
    prefix = items[0]
    for item in items[1:]:
        while not item.startswith(prefix):
            prefix = prefix[:-1]
    return prefix


def common(items: list[str]) -> str:
    return _common_prefix(items)


def common_legacy(items: list[str]) -> str:
    return _common_prefix(items)
