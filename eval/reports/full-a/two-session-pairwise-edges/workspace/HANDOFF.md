# Day 1 handoff

Implemented `pairs` in `solution.py` with the existing
`list[int] -> list[tuple[int, int]]` type hints.

## Design decisions

- Zip the input with its one-item-offset slice to produce overlapping adjacent
  tuples in input order, then materialize a new list.
- Empty and singleton inputs naturally produce `[]`.
- Reading and slicing the input preserves the caller's list. The implementation
  uses linear time and linear auxiliary space; no complexity constraint applies.
- Use only the Python standard library, compatible with Python 3.11+.

## Regression coverage and verification

`test_solution.py` contains five unittest methods covering overlap and order,
short inputs, exactly two items, duplicate and negative values, and input
preservation.

Run from the task workspace:

```sh
python -m unittest discover -v
```

Day 1 verification result: all five tests passed.

## Day 2 extension and verification

Added `pairs_many(cases: list[tuple]) -> list` in `solution.py`. Each tuple
is unpacked into one call to `pairs`, and results are collected in case order.
An empty batch returns `[]`. Exceptions are not caught, so the first exception
propagates unchanged and later cases are not called. Neither the batch nor its
arguments are modified. The day-1 `pairs` implementation and signature remain
unchanged.

Retained all five day-1 tests and added six batch tests for ordered results,
empty batches, preservation of cases and shared arguments, independent result
lists, unchanged exception identity and early termination, positional argument
unpacking, and invalid argument counts.

Verification command run from the task workspace:

```sh
python -m unittest discover -v
```

Observed result: exit code 0, `Ran 11 tests in 0.002s`, `OK`.
