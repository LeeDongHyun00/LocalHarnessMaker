"""Public task implementation."""


def partition(items: list[int]) -> tuple[list[int], list[int], list[int]]:
    """Return stable negative, zero, and positive partitions without mutation."""
    negatives: list[int] = []
    zeros: list[int] = []
    positives: list[int] = []
    for item in items:
        if item < 0:
            negatives.append(item)
        elif item == 0:
            zeros.append(item)
        else:
            positives.append(item)
    return negatives, zeros, positives
