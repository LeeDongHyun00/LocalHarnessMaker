"""Public task implementation."""


def common(items: list[str]) -> str:
    prefix = items[0] if items else ""
    for item in items[1:]:
        while not item.startswith(prefix):
            prefix = prefix[:-1]
        if not prefix:
            break
    return prefix
