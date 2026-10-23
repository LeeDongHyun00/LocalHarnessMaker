# Day 2 handoff

## Design decisions

- Preserved the existing public signature: `clamp(value: int, low: int, high: int) -> int`.
- Validate bounds first so `low > high` always raises `ValueError`, regardless of the value.
- Compare against each bound and return the corresponding bound or the unchanged value. Bounds are inclusive; equal bounds are valid.
- Added `clamp_many(cases: list[tuple]) -> list`, which calls `clamp(*case)` for each tuple in input order and returns the results as a list. Empty input returns `[]`.
- Batch processing stops at the first exception and propagates the same exception object unchanged. There is no exception wrapping or recovery.
- Neither function mutates cases or their arguments. Batch processing only iterates over cases and unpacks each tuple; the existing clamp only compares and returns inputs.
- Use only the standard library and Python 3.11+ compatible syntax.

## Verification

Run from the task workspace:

```sh
python -m unittest discover -v
```

Observed result: passed, exit code 0; `Ran 10 tests in 0.003s`, followed by `OK`.

The six Day 1 regression methods remain intact. Four batch methods cover ordered results, empty input, unchanged cases and tuples, invalid bounds, incorrect argument counts, and exception identity with no calls after the first failure.

Additional verification:

- `python -m py_compile solution.py` succeeded (exit code 0).
- The following test-method check passed (exit code 0), confirming at least three test methods and batch coverage:

```sh
python -c 'import ast; from pathlib import Path; tree = ast.parse(Path("test_solution.py").read_text()); methods = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test")]; assert len(methods) >= 3 and any("batch" in name.lower() or "many" in name.lower() for name in methods)'
```
