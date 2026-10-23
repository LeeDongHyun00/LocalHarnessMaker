"""Public task implementation."""

from collections.abc import Iterable
from typing import TypeVar


T = TypeVar("T")


def last_index(items: Iterable[T], target: T) -> int | None:
    """Return the last index equal to target, or None if there is no match."""
    result: int | None = None
    for index, item in enumerate(items):
        if item == target:
            result = index
    return result
