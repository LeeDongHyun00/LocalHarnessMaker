# Day 2 handoff

## Batch API extension

- Added `runs_many(cases: list[tuple]) -> list`, calling `runs(*case)` once
  per case in input order. Empty cases return `[]`; the first exception
  propagates unchanged and stops processing subsequent cases.
- Left the day-1 `runs` implementation and signature unchanged. The batch
  wrapper creates a new results list without modifying cases or arguments.
- Retained all six day-1 tests and added four batch tests covering order,
  input preservation, empty batches, positional argument unpacking, and
  exception identity with processing stopped at the first failure.

## Implementation and design decisions

- Preserved the existing public API: `runs(items: list[str]) -> list[tuple[str, int]]`.
- Scan input in order, incrementing the final output count only when the next
  string equals the current run's value. Nonadjacent equal strings stay separate.
- Build a new output list of tuples without modifying the input. An empty input
  naturally produces an empty list. Empty strings and Unicode use ordinary string
  equality.
- The implementation uses Python 3.11+ and only the standard library. It takes
  O(n) time and O(r) output space for n items and r runs.
- Six unittest regression methods cover empty input, adjacent runs, nonadjacent
  repeats, a single item, empty/Unicode strings, and input preservation.

## Verification (observed Day 2 results)

Run from the task workspace:

```sh
python -m py_compile solution.py test_solution.py
python -m unittest discover -v
```

- `python -m py_compile solution.py test_solution.py`: passed, exit code 0.
- `python -m unittest discover -v`: passed, exit code 0; observed
  `Ran 10 tests in 0.002s` followed by `OK`.
