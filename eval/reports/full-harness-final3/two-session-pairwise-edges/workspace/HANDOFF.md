# Day 2 handoff

## Design decisions

- Preserved the existing public API: `pairs(items: list[int]) -> list[tuple[int, int]]`.
- Read adjacent elements by index and collect tuples into a new list, preserving order and overlap without mutating the input.
- For empty and single-item inputs, the index range is empty, so the result is `[]`.
- Public unittest coverage includes short inputs, overlapping pairs, ordering, duplicate and negative values, and input preservation.
- The implementation uses only the Python standard library and is compatible with Python 3.11+.
- Added `pairs_many(cases: list[tuple]) -> list`, which calls `pairs(*case)` once per case in order and collects the results. Empty batches return `[]`; the first exception propagates unchanged and stops processing.
- The batch wrapper does not mutate cases or their arguments. The Day 1 `pairs` implementation and its six regression tests remain unchanged.
- Four batch tests cover ordered results and input preservation, empty batches, positional argument unpacking and call counts, and exception identity with processing stopped at the failing case.

## Verification

Run from the task workspace:

```sh
python -m py_compile solution.py
python -m unittest discover -v
```

Observed results after the Day 2 changes:

- `python -m py_compile solution.py`: exit code 0, no output.
- `python -m unittest discover -v`: exit code 0; `Ran 10 tests in 0.001s`, followed by `OK`. All six Day 1 tests and four batch tests passed.
