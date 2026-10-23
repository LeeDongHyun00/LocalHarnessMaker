"""Public task implementation."""

from collections.abc import Iterable
from typing import TypeVar


Left = TypeVar("Left")
Right = TypeVar("Right")


def interleave(left: Iterable[Left], right: Iterable[Right]) -> list[Left | Right]:
    """Return alternating left/right items, followed by any remaining items.

    Input collections are not modified. Iterator inputs are consumed.
    """
    left_items = iter(left)
    right_items = iter(right)
    result: list[Left | Right] = []

    while True:
        try:
            left_item = next(left_items)
        except StopIteration:
            result.extend(right_items)
            return result
        result.append(left_item)

        try:
            right_item = next(right_items)
        except StopIteration:
            result.extend(left_items)
            return result
        result.append(right_item)


def interleave_many(cases: list[tuple]) -> list:
    """Interleave each case in order, stopping at the first exception.

    Cases and input collections are not modified. As with interleave,
    iterator inputs are consumed.
    """
    return [interleave(*case) for case in cases]
