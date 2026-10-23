"""Public task implementation."""


def interleave(left: list[int], right: list[int]) -> list[int]:
    """Return a new list alternating left then right items.

    Append any remainder from the longer input in its original order.
    Empty inputs are valid. Preserve all values and each input's item order
    without mutating either input collection.
    """
    paired_length = min(len(left), len(right))
    result = [item for pair in zip(left, right) for item in pair]
    result.extend(left[paired_length:])
    result.extend(right[paired_length:])
    return result
