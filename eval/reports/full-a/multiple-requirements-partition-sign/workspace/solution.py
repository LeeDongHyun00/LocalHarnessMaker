"""Public task implementation."""


def partition(items: list[int]) -> tuple[list[int], list[int], list[int]]:
    """Return negatives, zeros, and positives as three lists in that order.

    Preserve input values, relative order, and duplicates in each partition
    without mutating the input collection.
    """
    negatives: list[int] = []
    zeros: list[int] = []
    positives: list[int] = []
    for item in items:
        if item < 0:
            negatives.append(item)
        elif item > 0:
            positives.append(item)
        else:
            zeros.append(item)
    return negatives, zeros, positives
