"""Public task implementation."""


def common(items: list[str]) -> str:
    if not items:
        return ''

    prefix = items[0]
    for item in items[1:]:
        length = 0
        while length < min(len(prefix), len(item)) and prefix[length] == item[length]:
            length += 1
        prefix = prefix[:length]
        if not prefix:
            break
    return prefix
