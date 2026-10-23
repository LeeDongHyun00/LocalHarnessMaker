# Day 2 handoff

Implemented `clamp(value: int, low: int, high: int) -> int` in `solution.py`.
Day 2 adds `clamp_many(cases: list[tuple]) -> list` while preserving the
day-1 function and its five regression tests unchanged.

## Design decisions

- Preserve the existing integer type hints and public function signature.
- Validate `low > high` first and raise `ValueError`, regardless of the value.
- Use `min(max(value, low), high)` to enforce inclusive bounds. Equal bounds
  are valid and always return the shared bound.
- The function has no side effects and does not mutate input collections.
- Use only the standard library. Public regression tests cover interior values,
  both out-of-range directions, inclusive endpoints, equal bounds, and reversed
  bounds.
- `clamp_many` unpacks each tuple into a call to `clamp`, returning results in
  input order and an empty list for empty input. It does not mutate cases or
  arguments, catch exceptions, or process further cases after an exception.
- Five batch tests cover ordering, empty input, mutable argument preservation,
  invalid bounds and arity, and propagation of the exact first exception object
  with no subsequent calls.

## Verification

Run from the task workspace with Python 3.11+:

```sh
python -m unittest discover -v
```

Observed in the runner-provided workspace after the Day 2 implementation:

```text
Ran 10 tests in 0.001s

OK
```

The command exited with status 0; all five day-1 tests and all five batch tests
passed.
