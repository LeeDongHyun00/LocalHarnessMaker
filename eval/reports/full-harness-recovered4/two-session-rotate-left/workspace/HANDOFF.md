# Day 2 handoff

## Design decisions

- Preserved the public signature `rotate(items: list[int], steps: int) -> list[int]`.
- Handle empty input before modulo to avoid division by zero.
- Normalize steps with Python's modulo operation; negative values therefore rotate right.
- Concatenate list slices to return a fresh list without mutating the input, including zero and full rotations. This takes O(n) time and O(n) additional space.
- Regression tests cover positive and negative wrapping, empty input, zero and full rotations, singleton input, and input preservation/result independence.
- Added `rotate_many(cases: list[tuple]) -> list`, which calls `rotate(*case)` in input order and returns a list of results. Empty batches return `[]`.
- The batch implementation does not modify cases or their arguments. Exceptions are not caught, so the first exception propagates unchanged and later cases are not evaluated.
- Added batch tests for result order, input preservation and fresh results, empty batches, exception identity and stopping at the first failure, and invalid positional argument counts. All six day-1 test methods remain intact.

## Verification

Run from the task workspace using Python 3.11+:

```sh
python -m unittest discover -v
python -m py_compile solution.py test_solution.py
```

Observed verification results on 2026-10-23:

- `python -m unittest discover -v`: passed, exit code 0; `Ran 10 tests in 0.002s`, followed by `OK`.
- `python -m py_compile solution.py test_solution.py`: successful, exit code 0, with no output.
