# Day 1 handoff

Implemented `windows(items: list[int], size: int) -> list[list[int]]`.

Design decisions:
- Validate `size` before inspecting available windows, so nonpositive sizes raise
  `ValueError` even for empty input.
- Slice at each start index from zero through `len(items) - size`, inclusive.
  This produces only full windows and advances by one. Oversized windows and
  empty input with a positive size naturally produce an empty list.
- Preserve the supplied type hints. Each slice creates a new list, leaving the
  input unchanged and making returned windows independent of one another.
- Use only the Python standard library; no complexity optimization is required.

Regression coverage in `test_solution.py` includes overlapping windows, unit and
full-length sizes, oversized sizes, empty input, invalid sizes, input preservation,
and independent result lists.

Verification command (run from the task workspace with Python 3.11+):

```sh
python -m unittest discover -v
```

Day 1 verification: all 5 tests passed using Python 3.13.5.

## Day 2 handoff

Added `windows_many(cases: list[tuple]) -> list` to `solution.py`.
Each tuple is unpacked as positional arguments to `windows`, with results
collected in case order. An empty batch returns `[]`. Exceptions are not caught,
so the first exception propagates unchanged and no later case is evaluated.
The batch function does not mutate cases or their arguments. The day-1
`windows` implementation and all five existing regression tests are unchanged.

Added five unittest methods covering ordered batch results, empty batches,
preservation of cases and shared arguments, independent results, exception
identity and stopping at the first failure, and validation/argument-count errors.

Day 2 verification command, run from the runner-provided workspace:

```sh
python -m unittest discover -v
```

Observed result: exit code 0; `Ran 10 tests in 0.001s`, followed by `OK`.
All five day-1 tests and all five batch tests passed.
