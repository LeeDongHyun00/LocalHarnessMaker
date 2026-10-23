# Day 2 handoff

## design decisions

- Preserve the existing `dict[str, str] -> dict[str, list[str]]` type hints.
- Iterate through input dictionary items and append each key to its value's group.
  Dictionary iteration preserves insertion order within each resulting list.
- Allocate a fresh result dictionary and fresh lists on every call; the input is
  never modified. Empty input naturally produces `{}`.
- Use only the Python 3.11+ standard library.
- Keep the Day 1 `invert` API unchanged. Add
  `invert_many(cases: list[tuple]) -> list`, expanding each tuple as positional
  arguments to `invert` in case order. Empty cases return `[]`.
- The batch wrapper does not mutate the cases or their arguments. Exceptions
  propagate unchanged and stop processing before subsequent cases are called.

## Verification

Run from the task workspace:

```sh
python -m unittest discover -v
```

Regression tests cover grouping, insertion order, empty input, input preservation,
and independent results across calls.

Observed verification result: `Ran 8 tests in 0.001s`, `OK` (exit code 0).
The suite includes four batch tests covering result order, empty cases, unchanged
inputs and independent results, positional argument forwarding, exception object
identity, and stopping at the first exception.

Additional verification commands, both observed to exit with code 0:

```sh
python -m py_compile solution.py
python -c 'import ast; from pathlib import Path; tree = ast.parse(Path("test_solution.py").read_text()); assert sum(isinstance(n, ast.FunctionDef) and n.name.startswith("test") for n in ast.walk(tree)) >= 3'
```
