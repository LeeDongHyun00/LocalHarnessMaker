# Day 2 handoff

## Design decisions

- Preserve the existing typed API: `partition(items: list[int]) -> tuple[list[int], list[int], list[int]]`.
- Return a tuple containing three fresh lists in negative, zero, positive order.
- Iterate through the input once and append each value to its partition, preserving relative order and duplicates without mutating the input.
- Use Python 3.11+ and only the standard library. No additional input validation is needed for the declared integer API.
- Public unittest coverage checks mixed values, order and duplicates, empty input, single-partition inputs, input preservation, and independent output lists.
- Added `partition_many(cases: list[tuple]) -> list`, calling `partition(*case)` once per case in input order. An empty batch returns `[]`; the first exception propagates unchanged and stops processing. Neither cases nor arguments are mutated.
- Batch tests cover ordered results, positional argument expansion, empty batches, input preservation, independent results, and exception identity with no subsequent calls.

## Verification

Run from the task workspace:

```sh
python -m py_compile solution.py test_solution.py
python -m unittest discover -v
```

Observed results from the task workspace:

- `python -m py_compile solution.py test_solution.py`: exit code 0, no output.
- `python -m unittest discover -v`: exit code 0; `Ran 8 tests in 0.002s`, followed by `OK` (all eight test methods passed).
