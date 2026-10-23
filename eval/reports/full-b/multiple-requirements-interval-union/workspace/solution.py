"""Public task implementation."""


def union(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge overlapping or touching closed intervals, sorted by start.

    Each input tuple contains a start and an end. Raise ValueError if any
    start is greater than its end. Empty input returns an empty list.
    Preserve endpoint values and leave the input collection and its order
    unchanged.
    """
    merged: list[tuple[int, int]] = []
    for start, end in sorted(intervals, key=lambda interval: interval[0]):
        if start > end:
            raise ValueError("Interval start must not be greater than its end")

        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        elif end > merged[-1][1]:
            merged[-1] = (merged[-1][0], end)

    return merged
