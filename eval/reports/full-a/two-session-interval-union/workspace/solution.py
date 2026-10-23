"""Public task implementation."""


def union(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return sorted unions of overlapping or touching closed intervals.

    Raise ValueError for reversed endpoints, without changing the input.
    """
    for start, end in intervals:
        if start > end:
            raise ValueError("interval start must be less than or equal to end")

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

    Leave inputs unchanged and propagate the first exception immediately.
    """
    return [union(*case) for case in cases]
