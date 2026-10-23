"""Public task implementation."""


def interleave(left: list[int], right: list[int]) -> list[int]:
    """Alternate items from left and right, then append any remaining items."""
    result: list[int] = []
    shared_length = min(len(left), len(right))
    for index in range(shared_length):
        result.append(left[index])
        result.append(right[index])
    result.extend(left[shared_length:])
    result.extend(right[shared_length:])
    return result
