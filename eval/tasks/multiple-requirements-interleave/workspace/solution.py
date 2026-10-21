"""Public task implementation."""


def interleave(left: list[int], right: list[int]) -> list[int]:
    return [item for pair in zip(left, right) for item in pair]
