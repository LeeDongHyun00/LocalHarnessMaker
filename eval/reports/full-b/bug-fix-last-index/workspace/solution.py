"""Public task implementation."""


def last_index(items: list[str], target: str) -> int | None:
    for index in range(len(items) - 1, -1, -1):
        if items[index] == target:
            return index
    return None
