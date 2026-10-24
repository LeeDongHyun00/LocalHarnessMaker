"""Public task implementation."""


def interleave(left: list[int], right: list[int]) -> list[int]:
    """Alternate left then right items, preserving their values and order.

    Append the longer input's remainder in order. Either or both inputs may be
    empty. Return a new list without mutating either input collection.
    """
    result = [item for pair in zip(left, right) for item in pair]
    paired_count = min(len(left), len(right))
    result.extend(left[paired_count:])
    result.extend(right[paired_count:])
    return result
