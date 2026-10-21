"""Public task implementation."""


def last_index(items: list[str], target: str) -> int | None:
    for i in range(len(items) - 1, -1, -1):
        if items[i] == target: return i
    return None


def last_index_legacy(items: list[str], target: str) -> int | None:
    for i in range(len(items) - 1, -1, -1):
        if items[i] == target: return i
    return None
