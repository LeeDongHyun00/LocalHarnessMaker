"""Public task implementation."""


def interleave(left: list[int], right: list[int]) -> list[int]:
    """Return a new list alternating left items then right items.

    Append any remainder from the longer input in its original order.
    Empty inputs are valid. Preserve input values and the order within each
    input, without mutating either input collection.
    """
    shared_length = min(len(left), len(right))
    result = [item for pair in zip(left, right) for item in pair]
    result.extend(left[shared_length:])
    result.extend(right[shared_length:])
    return result
