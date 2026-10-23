# Day 1 handoff

Implemented `solution.union` with the existing typed public signature, using
Python 3.11+ and only the standard library.

## Design decisions

- Validate every interval before merging so a reversed interval raises
  `ValueError`, including one contained within an otherwise valid interval.
- Sort a copy by start (then end) and scan into a new result list. Input
  collections are never modified, including when validation fails.
- Closed intervals merge when the next start is less than or equal to the
  current end. Shared endpoints count as touching; a positive gap remains
  separate. Point intervals are valid.
- Keep the maximum end when merging to handle nested and duplicate intervals.
- Empty input naturally returns a new empty list.
- Sorting takes O(n log n) time; auxiliary storage is O(n).

## Verification

From the task workspace, run:

```sh
python -m unittest discover -v
```

Day 1 result: all 7 unittest methods passed.

Regression coverage in `test_solution.py` covers empty input, unsorted overlap
and touching chains, sorted disjoint output, nested and duplicate intervals,
point intervals, negative endpoints, invalid intervals, and input preservation.

## Day 2 extension

Added `solution.union_many(cases: list[tuple]) -> list`. Each case is expanded
as positional arguments to `union`, and results are returned in case order.
Empty cases return `[]`. The first exception propagates unchanged and prevents
later cases from running. Neither the cases nor their arguments are modified.
The day-1 `union` implementation and signature remain unchanged.

Added five batch unittest methods covering empty batches, ordered results,
repeated inputs and independent results, input preservation on success and
failure, exception identity and early termination, and positional argument
expansion (including invalid arity). All seven day-1 tests remain in place.

Verification command run from the task workspace:

```sh
python -m unittest discover -v
```

Observed day-2 result: exit code 0; `Ran 12 tests in 0.002s`, followed by `OK`.
All 12 unittest methods in `test_solution.py` passed.
