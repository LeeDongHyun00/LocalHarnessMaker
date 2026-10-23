# Day 1 handoff

Implemented `prefix(items: list[int]) -> list[int]` in `solution.py`.

## Design decisions

- Accumulate a running total and append it once per input element, producing inclusive prefix sums with the same length as the input.
- Start the total at zero so empty input naturally returns `[]` and negative values and zero work without special cases.
- Build a fresh result list and only read the input, preserving the caller's collection.
- Preserve the public type hints and use only Python 3.11+ standard library features. The implementation uses O(n) time and O(n) result space.

## Verification

Run from the task workspace:

```sh
python -m unittest discover -v
```

`test_solution.py` covers positive values, empty input, negative values and zero, a single element, and input preservation/result independence.

## Day 2 extension

Added `prefix_many(cases: list[tuple]) -> list` in `solution.py`.
Each tuple is unpacked into positional arguments for `prefix`, with results
collected in case order. An empty batch returns `[]`. Exceptions are not caught,
so the first exception propagates unchanged and subsequent cases are not called.
The day-1 `prefix` implementation and signature are unchanged. The batch function
only reads cases and their arguments, and each successful call produces a fresh
result list.

Added five batch unittest methods covering ordered results, empty batches,
preservation of cases and shared arguments, independent results, exception object
identity and stopping at the first failure, and invalid positional argument counts.
All five day-1 regression test methods remain.

### Day 2 verification evidence

Command run from the runner-provided workspace:

```sh
python -m unittest discover -v
```

Observed result (exit code 0):

```text
Ran 10 tests in 0.001s

OK
```
