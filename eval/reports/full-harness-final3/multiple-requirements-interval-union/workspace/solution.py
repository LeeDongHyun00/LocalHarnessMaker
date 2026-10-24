"""Public task implementation."""


def union(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge overlapping or touching closed intervals, sorted by start.

    Raise ValueError if any interval's start is greater than its end.
    Return [] for empty input. Do not mutate the input collection, its
    interval values, or its order.
    """
    for start, end in intervals:
        if start > end:
            raise ValueError("interval start must not exceed its end")

    merged: list[tuple[int, int]] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
