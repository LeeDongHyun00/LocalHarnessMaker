"""Public task implementation."""


def union(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return the sorted union of closed intervals without changing the input.

    Intervals sharing an endpoint merge. Any reversed interval raises ValueError.
    """
    for start, end in intervals:
        if start > end:
            raise ValueError(f"Interval start {start} exceeds end {end}")

    merged: list[tuple[int, int]] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            previous_start, previous_end = merged[-1]
            merged[-1] = (previous_start, max(previous_end, end))
        else:
            merged.append((start, end))
    return merged


def union_many(cases: list[tuple]) -> list:
    """Call union with each case's positional arguments, in order.

    Inputs are left unchanged and the first exception propagates to the caller.
    """
    return [union(*case) for case in cases]
