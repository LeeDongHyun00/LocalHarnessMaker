"""Public task implementation."""


def partition(items: list[int]) -> tuple[list[int], list[int], list[int]]:
    """Return negative, zero, and positive values as three lists in that order.

    Preserve the original values, relative order, and duplicates within each
    partition. Return new lists without mutating the input collection.
    """
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
