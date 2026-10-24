# Day 1 handoff

## Design decisions

- Preserve the supplied public API: `union(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]`.
- Validate every interval before merging; raise `ValueError` when `start > end`.
- Sort a new list, then accumulate new tuples in a separate result list so input collections remain unchanged.
- Merge when the next start is at most the current end. Closed intervals sharing an endpoint touch; integer neighbors such as `(1, 2)` and `(3, 4)` remain separate.
- Extend merged ends with `max` to handle nested intervals. Empty input naturally returns a new empty list.
- Sorting takes O(n log n) time; additional space is O(n).

## Verification

Use Python 3.11+ and the standard library:

```sh
python -m unittest discover -v
```

The six regression tests cover overlapping and touching intervals, sorted disjoint output, nesting, duplicates, point intervals, empty input, invalid intervals, and input immutability.

## Day 2 extension

- Added `union_many(cases: list[tuple]) -> list`, which calls `union(*case)` for each tuple in input order and collects the results. Empty input returns `[]`.
- The existing `union` implementation and signature are unchanged. The batch function does not mutate cases or arguments and lets the first exception propagate unchanged, stopping further calls.
- Added four batch tests covering result order, empty input without calls, input immutability on success and failure, exception identity, and stopping at the first failure.

### Observed verification

- `python -m unittest discover -v` — exit code 0; `Ran 10 tests in 0.002s`, `OK` (six day-1 tests and four batch tests).
- `python -m py_compile solution.py` — exit code 0; compilation succeeded.
- An AST check confirmed 10 unittest test methods, including methods named with `many`.
