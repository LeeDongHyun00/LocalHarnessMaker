"""Public task implementation."""

from collections.abc import Iterable


def unique(items: Iterable[str]) -> list[str]:
    """Return distinct strings in first-occurrence order without modifying items."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def unique_many(cases: list[tuple]) -> list:
    """Call unique with each case's arguments in order, stopping on any exception."""
    return [unique(*case) for case in cases]
