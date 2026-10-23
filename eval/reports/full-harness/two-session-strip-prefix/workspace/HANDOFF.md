# Day 2 handoff

## design decisions

- Preserve the public signature `strip_prefix(text: str, prefix: str) -> str`.
- Use the standard library's `str.removeprefix`, available in Python 3.11+,
  to remove exactly one literal matching prefix. Empty and nonmatching prefixes
  leave the text unchanged; repeated prefixes are removed only once.
- Strings are immutable, and the implementation does not mutate inputs.
- Add `strip_prefix_many(cases: list[tuple]) -> list`, forwarding each tuple
  as positional arguments to `strip_prefix`. Results preserve case order;
  an empty input returns `[]`. No exceptions are caught, so the first exception
  propagates unchanged and later cases are not processed. The input list and
  its argument tuples are not modified.
- Public unittest coverage checks matching, nonmatching, empty, repeated,
  character-set regression, full-match, empty-text, and Unicode cases.
- Batch coverage checks ordered results, unchanged inputs, empty batches,
  invalid arguments, exception identity, and stopping at the first exception.

## Verification

Executed from the task workspace on 2026-10-23:

```sh
python -m py_compile solution.py
python -m unittest discover -v
```

Observed results:

- `python -m py_compile solution.py`: exit code 0, no output.
- `python -m unittest discover -v`: exit code 0; `Ran 11 tests in 0.002s`,
  followed by `OK`. All seven day-1 tests and four batch tests passed.
- The following test-method count check exited with code 0 and no output
  (11 test methods are present, meeting the minimum of three):

```sh
python -c 'import ast; from pathlib import Path; tree = ast.parse(Path("test_solution.py").read_text()); assert sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test") for n in ast.walk(tree)) >= 3'
```
