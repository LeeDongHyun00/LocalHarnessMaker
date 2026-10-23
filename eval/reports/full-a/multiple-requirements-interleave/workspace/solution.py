"""Public task implementation."""


def interleave(left: list[int], right: list[int]) -> list[int]:
    """Return a new list alternating left then right items in input order.

    Append any remainder from the longer input in order. Either input may be
    empty. Preserve all input values and leave both input collections unchanged.
    """
    shared_length = min(len(left), len(right))
    result = [item for pair in zip(left, right) for item in pair]
    result.extend(left[shared_length:])
    result.extend(right[shared_length:])
    return result
