# Day 1 and Day 2 handoff

Implemented `merge(left, right)` in `solution.py` with the existing
`dict[str, int]` type hints.

## Design decisions

- Copy the left dictionary, then add every right-hand count using a default of
  zero for missing keys. This returns the union of keys and sums shared counts.
- Keep all entries, including zero and negative totals. Avoid count-collection
  operations that could discard nonpositive values.
- Return a fresh dictionary and never write to either input. Passing the same
  dictionary for both inputs is supported.
- Use only the standard library and Python 3.11+ compatible syntax.

## Verification

Run from the task workspace:

```sh
python -m unittest discover -v
```

Regression coverage includes shared and disjoint keys, zero and negative totals,
empty inputs, result independence, unchanged inputs, and aliased inputs.

Day 1 verification result: all 5 unittest test methods passed with the command
above. No known unfinished work remains for the requested public behavior.

## Day 2 extension

Added `merge_many(cases: list[tuple]) -> list` in `solution.py`. Each tuple is
unpacked as positional arguments to the existing `merge`, and results are
returned in case order. An empty batch returns `[]`. Exceptions are not caught,
so the first exception propagates unchanged and later cases are not called.
Neither the batch nor its argument dictionaries are modified. The Day 1
`merge` implementation and its five regression test methods remain unchanged.

Added five batch test methods in `test_solution.py`, covering ordered results,
empty batches, unchanged and aliased inputs, independent results, exception
identity and stopping at the first failure, and invalid positional arity.

Day 2 verification command, run from the task workspace:

```sh
python -m unittest discover -v
```

Observed result: exit code 0; `Ran 10 tests in 0.001s`, followed by `OK`.
All 10 unittest test methods passed, including all five Day 1 regression tests
and all five batch tests. No known unfinished work remains.
