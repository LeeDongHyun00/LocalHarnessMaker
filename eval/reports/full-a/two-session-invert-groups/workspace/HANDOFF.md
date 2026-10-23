# Day 1 handoff

Implemented `invert` in `solution.py` and added public API regression tests in
`test_solution.py`.

## Design decisions

- Preserve the existing `dict[str, str] -> dict[str, list[str]]` type hints.
- Iterate over input dictionary entries in insertion order and append each key
  to the list for its value. Group order also follows first appearance of values.
- Build a fresh dictionary and fresh lists for each call; never mutate the input.
- Empty input naturally produces an empty dictionary. Empty strings are ordinary
  keys and values.
- Use only the Python standard library, compatible with Python 3.11+.

## Verification

Run from the task workspace:

```sh
python -m unittest discover -v
```

Day 1 result: all 5 tests passed using Python 3.13.5.

Coverage includes empty input, distinct values, interleaved repeated values and
key order, empty strings, input preservation, and independent results.

## Day 2 extension

Added `invert_many(cases: list[tuple]) -> list` to `solution.py`. Each tuple is
unpacked as positional arguments to `invert`, with results collected in case
order. An empty batch returns `[]`. Exceptions propagate unchanged and stop
processing immediately. The batch and its arguments are never mutated.
The Day 1 `invert` implementation and its five regression tests remain intact.

Added five batch test methods covering empty batches, ordered results, preserved
cases and arguments, independent results for repeated arguments, exception
identity and early termination, and invalid positional argument counts.

Day 2 verification command, run from the task workspace:

```sh
python -m unittest discover -v
```

Observed result: `Ran 10 tests in 0.002s`, followed by `OK` (exit code 0).
All five Day 1 tests and all five batch tests passed.
