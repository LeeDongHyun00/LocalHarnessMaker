"""Public task implementation."""


def _union(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    for start, end in sorted(intervals):
        if start > end:
            raise ValueError('reversed interval')
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0], max(result[-1][1], end))
        else:
            result.append((start, end))
    return result


def union(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    return _union(intervals)


def union_legacy(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    return _union(intervals)
