"""Public task implementation."""


def last_index(items: list[str], target: str) -> int | None:
    return items.index(target) if target in items else None
