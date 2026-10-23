"""Public task implementation."""


def interleave(left: list[int], right: list[int]) -> list[int]:
    result = [item for pair in zip(left, right) for item in pair]
    shared_length = min(len(left), len(right))
    result.extend(left[shared_length:])
    result.extend(right[shared_length:])
    return result
