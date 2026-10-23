"""Public task implementation."""


def union(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return sorted, merged closed intervals without modifying the input.

    Overlapping intervals and intervals sharing an endpoint are merged.
    Raise ValueError if any interval's start is greater than its end.
    """
    for start, end in intervals:
        if start > end:
            raise ValueError("Interval start must not exceed its end")

    merged: list[tuple[int, int]] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            previous_start, previous_end = merged[-1]
            merged[-1] = (previous_start, max(previous_end, end))
        else:
            merged.append((start, end))
    return merged
