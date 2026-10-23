# Day 2 handoff

## Design decisions

- Preserve the existing typed public API: `prefix(items: list[int]) -> list[int]`.
- Accumulate a running total and append it after each input value, producing inclusive prefix sums with the same length as the input.
- Return a fresh list without changing the input. Empty input naturally returns `[]`; negative values and zeros use ordinary integer addition.
- The implementation uses only the Python standard library and takes O(n) time and O(n) space for the returned list.
- Six unittest methods cover positive, empty, negative, mixed/zero, single-item, and input-preservation behavior.
- Add `prefix_many(cases: list[tuple]) -> list`, calling `prefix(*case)` once per tuple in input order. Empty input returns `[]`; the first exception propagates unchanged and stops further calls.
- The batch wrapper does not mutate cases or arguments; the day-1 `prefix` implementation and signature remain unchanged.
- Four additional unittest methods cover batch results and input preservation, empty batches, positional argument forwarding and call order, and exception identity with immediate termination.

## Verification

Run from the task workspace using Python 3.11+:

```sh
python -m unittest discover -v
python -m py_compile solution.py test_solution.py
```

Observed results after the day-2 changes:

- `python -m unittest discover -v`: exit code 0; ran 10 tests in 0.002s; `OK` (all passed).
- `python -m py_compile solution.py test_solution.py`: exit code 0; completed successfully with no output.
