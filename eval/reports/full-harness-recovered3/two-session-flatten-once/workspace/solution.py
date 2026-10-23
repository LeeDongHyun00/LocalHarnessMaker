"""Public task implementation."""

from typing import TypeVar


T = TypeVar("T")


def flatten(items: list[list[T]]) -> list[T]:
    """Return elements from each inner list in order, flattening one level."""
    return [element for inner in items for element in inner]


def flatten_many(cases: list[tuple]) -> list:
    """Call flatten with each case's positional arguments, in order."""
    return [flatten(*case) for case in cases]
