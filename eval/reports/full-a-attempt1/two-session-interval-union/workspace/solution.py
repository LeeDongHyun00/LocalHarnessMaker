"""Public task implementation."""


def union(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return the sorted union of closed intervals without changing the input.

    Raise ValueError if any interval has its start after its end.
    """
    for start, end in intervals:
        if start > end:
            raise ValueError("interval start must not exceed its end")

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

    Leave cases and their arguments unchanged. Stop at the first exception
    and let it propagate unchanged.
    """
    return [union(*case) for case in cases]
