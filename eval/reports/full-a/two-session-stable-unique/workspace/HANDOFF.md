# Day 1 handoff

Implemented `unique(items: list[str]) -> list[str]` in `solution.py`.

## Design decisions

- Use `dict.fromkeys(items)` to remove duplicates while preserving insertion
  order, which Python 3.11+ guarantees.
- String keys use case-sensitive equality; no normalization is applied.
- Convert the dictionary keys to a new list, leaving the input unchanged.
- Empty input naturally produces an empty list. No dependencies are required.

## Verification

Run from the task workspace with Python 3.11+:

```sh
python -m unittest discover -v
```

`test_solution.py` covers empty input, duplicate ordering, case sensitivity,
input preservation and result independence, empty strings, and distinct input.

Day 1 result: all 6 tests passed using Python 3.13.5 and the command above.

## Day 2: batch API

Added `unique_many(cases: list[tuple]) -> list` in `solution.py` while leaving
the day-1 `unique` API unchanged. Each tuple is unpacked as positional arguments
to `unique`, and results retain case order. Empty cases return `[]`. Calls run
sequentially; the first exception propagates unchanged and later cases are not
called. Neither the cases nor their arguments are modified.

Added five batch test methods covering empty cases, ordered results, input
preservation, independent results, exception identity and early stopping,
invalid argument counts, and underlying `unique` failures. All six day-1 test
methods remain in `test_solution.py`.

Verification command run from the task workspace:

```sh
python -m unittest discover -v
```

Observed Day 2 result: exit code 0; `Ran 11 tests in 0.002s`, followed by `OK`.
All 11 unittest test methods passed, including the five batch tests.
