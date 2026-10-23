"""Public task implementation."""


def partition(items: list[int]) -> tuple[list[int], list[int], list[int]]:
    """Return new lists of negative, zero, and positive items in input order."""
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


def partition_many(cases: list[tuple]) -> list:
    """Partition each case in order, propagating the first exception unchanged."""
    return [partition(*case) for case in cases]
