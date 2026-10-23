# Day 2 handoff

Implemented `runs(items: list[str]) -> list[tuple[str, int]]` using only
Python 3.11+ standard-library features.

Extended the public API with `runs_many(cases: list[tuple]) -> list`.
Each tuple is unpacked as positional arguments to `runs`. Results preserve case
order, and an empty case list returns `[]`. The first exception propagates as
the original exception object, and later cases are not called. Neither the
case list nor its argument lists are modified. The day-1 `runs` API is unchanged.

## Design decisions

- Scan the input in order and compare each string with the last output run.
  Increment that run's count when equal; otherwise append a new run.
- Compare strings by equality. Nonadjacent equal strings remain separate runs;
  empty strings and Unicode strings receive the same treatment as other values.
- Build a fresh result list and never modify the input. Empty input naturally
  returns an empty list. Preserve the supplied public signature and type hints.
- The implementation takes O(n) time and O(r) output space for r runs.

## Verification

Run from the task workspace with Python 3.11 or newer:

```sh
python -m unittest discover -v
```

Observed result on day 2: exit code 0, `Ran 11 tests in 0.001s`, `OK`.

`test_solution.py` retains all six day-1 regression tests covering empty input,
a single value, adjacent repetitions, separated repetitions, empty/Unicode
strings, and input preservation. Five batch tests cover empty cases, result
ordering, case/argument preservation and independent results, exception identity
and stopping at the first failure, and invalid positional argument counts.
