"""Public task implementation."""


def partition(items: list[int]) -> tuple[list[int], list[int], list[int]]:
    """Return (negatives, zeros, positives) as three new lists.

    Preserve the original values, relative order, and duplicates within each
    partition. Do not mutate the input collection.
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
