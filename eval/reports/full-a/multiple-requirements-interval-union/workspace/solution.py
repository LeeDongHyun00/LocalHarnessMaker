"""Public task implementation."""


def union(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge overlapping or touching closed intervals, sorted by start.

    Raise ValueError if any interval has start > end. Empty input returns
    an empty list. Preserve endpoint values without modifying the input
    collection, its order, or its intervals.
    """
    for start, end in intervals:
        if start > end:
            raise ValueError("interval start must not exceed its end")

    merged: list[tuple[int, int]] = []
    for start, end in sorted(intervals, key=lambda interval: interval[0]):
        if merged and start <= merged[-1][1]:
            previous_start, previous_end = merged[-1]
            merged[-1] = (previous_start, max(previous_end, end))
        else:
            merged.append((start, end))
    return merged
