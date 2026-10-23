"""Public task implementation."""


def interleave(left: list[int], right: list[int]) -> list[int]:
    """Alternate left and right items, then append the longer input's tail."""
    result: list[int] = []
    shared_length = min(len(left), len(right))
    for index in range(shared_length):
        result.append(left[index])
        result.append(right[index])
    result.extend(left[shared_length:])
    result.extend(right[shared_length:])
    return result


def interleave_many(cases: list[tuple]) -> list:
    """Call interleave with each case's arguments, stopping at the first error."""
    return [interleave(*case) for case in cases]
