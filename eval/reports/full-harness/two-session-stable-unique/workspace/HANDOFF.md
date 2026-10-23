# Day 2 handoff

## Design decisions

- `unique` accepts an `Iterable[str]` and returns a fresh `list[str]`.
- A local set tracks strings already encountered; a separate list preserves first-occurrence order.
- Standard string equality keeps comparisons case-sensitive, including empty strings.
- The function does not modify input collections. Iterator inputs are consumed once.
- The implementation uses only the Python 3.11+ standard library.
- `unique_many(cases: list[tuple]) -> list` calls `unique(*case)` for each case
  in order and returns the collected results, or `[]` for no cases.
- Batch processing does not modify cases or argument collections. As with
  `unique`, iterator arguments are consumed. The first exception propagates
  unchanged and later cases are not called.
- The Day 1 `unique` implementation and signature are unchanged.

## Verification

Run from the task workspace:

```sh
python -m unittest discover -v
```

Observed result: all 8 tests passed (`Ran 8 tests in 0.001s`, `OK`); exit code 0.

Additional verification: `python -m py_compile solution.py` exited with code 0.
An AST check of `test_solution.py` confirmed at least three test methods and a
method containing `many`; exit code 0.

Regression coverage includes duplicate removal and order, empty input, case sensitivity,
empty strings, input non-mutation, tuples, and generators.
Batch coverage includes result order, empty cases, unchanged inputs, positional
argument forwarding, exception identity, and stopping at the first failure.
