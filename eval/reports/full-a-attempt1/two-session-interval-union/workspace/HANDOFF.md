# Day 2 handoff

Added `union_many(cases: list[tuple]) -> list` in `solution.py`. Each tuple
is unpacked as positional arguments to `union`, with results collected in case
order. An empty batch returns `[]`. Exceptions propagate directly, preserving
the exception object and stopping before later cases. Cases and their arguments
are not mutated. The day-1 `union` implementation and signature are unchanged.

## Day 2 verification evidence

Ran from the runner-provided workspace:

```sh
python -m unittest discover -v
```

Observed result: exit code 0; `Ran 11 tests in 0.002s`, followed by `OK`.
All six day-1 tests and five new batch test methods passed. Batch coverage
includes case order, empty batches, positional unpacking, input preservation,
independent results, unchanged exception identity, stopping on the first error,
and propagation of validation and argument-count errors.

## Day 1 implementation notes

Implemented `union` in `solution.py` with its existing typed public API.

## Design decisions

- Validate all intervals before merging; any `start > end` raises `ValueError`,
  including invalid intervals contained within an otherwise valid interval.
- Sort a copy, then scan into a fresh result list to preserve the input.
- Closed intervals merge when the next start is at most the current end.
  Equal endpoints touch; a positive gap remains separate, even for adjacent
  integer endpoints such as `(1, 2)` and `(3, 4)`.
- Extend merged ends with `max` so nested and duplicate intervals work correctly.
- Empty input returns a fresh empty list. Point intervals and negative endpoints
  are supported. Runtime is O(n log n), with O(n) additional space.
- Use Python 3.11+ and only the standard library.

## Verification

Run from the task workspace:

```sh
python -m unittest discover -v
```

The six regression test methods cover empty input, unsorted overlapping and
touching chains, sorted disjoint output, nesting, duplicates, negative and point
intervals, invalid intervals, and input preservation on success and failure.
