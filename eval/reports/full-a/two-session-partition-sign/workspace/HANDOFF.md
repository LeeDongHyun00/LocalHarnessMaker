# Day 1 handoff

Implemented `partition` in `solution.py` with its existing type hints and public
signature: `list[int]` input and a tuple of three `list[int]` results.

## Design decisions

- Traverse the input once, appending each integer to a fresh negative, zero, or
  positive list. Return those lists in that order.
- Appending in traversal order preserves relative order and duplicates.
- Never modify the input or reuse it as an output list. Each result list is
  independent, including for empty input and repeated calls.
- Use only Python 3.11+ and the standard library. The implementation takes O(n)
  time and O(n) output space, although no complexity constraint was required.

## Regression coverage and verification

`test_solution.py` contains four unittest methods covering mixed values with
duplicates, empty input, inputs containing only one sign category, and input
preservation plus output independence.

Run from the task workspace:

```sh
python -m unittest discover -v
```

Day 1 verification result: all four tests passed.

## Day 2: batch API

Added `partition_many(cases: list[tuple]) -> list` in `solution.py`. Each tuple
is unpacked as positional arguments to `partition`. Results preserve case order,
and an empty batch returns `[]`. The first exception propagates unchanged and
stops evaluation of later cases. Neither the batch nor its arguments are mutated.
The Day 1 `partition` signature and implementation remain unchanged.

Retained all four Day 1 unittest methods and added five batch methods covering
ordered results, empty batches, input preservation and independent results,
exception identity and stopping at the first failure, and invalid argument counts.

Day 2 verification command, run from the task workspace:

```sh
python -m unittest discover -v
```

Observed result: exit code 0; `Ran 9 tests in 0.002s`, followed by `OK`.
All nine unittest methods passed, including the four Day 1 regression tests.
