"""Public task implementation."""


def interleave(left: list[int], right: list[int]) -> list[int]:
    result: list[int] = []
    for i in range(max(len(left), len(right))):
        if i < len(left): result.append(left[i])
        if i < len(right): result.append(right[i])
    return result


def interleave_legacy(left: list[int], right: list[int]) -> list[int]:
    result: list[int] = []
    for i in range(max(len(left), len(right))):
        if i < len(left): result.append(left[i])
        if i < len(right): result.append(right[i])
    return result
