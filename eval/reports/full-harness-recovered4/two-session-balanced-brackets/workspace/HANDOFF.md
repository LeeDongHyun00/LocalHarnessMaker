# Day 2 handoff

## Day 2 extension

- Added `balanced_many(cases: list[tuple]) -> list`, calling `balanced(*arguments)`
  once per case in order. Empty input returns `[]`.
- The batch function does not modify cases or their argument tuples and lets the
  first exception propagate unchanged, without processing later cases.
- The Day 1 `balanced` implementation and its five regression tests are unchanged.
- Added four batch tests covering ordered results, unchanged inputs, empty input,
  positional forwarding, and exception identity with immediate stopping.

## design decisions

- Preserve the public API `balanced(text: str) -> bool`.
- Use a local stack of opening brackets. Each closing bracket must match the
  most recent opener; an empty stack or a mismatch returns `False` immediately.
- Ignore every character except `()`, `[]`, and `{}`, including quote characters.
  Brackets inside quotes still count because this checks text, not source syntax.
- Return `True` only when the stack is empty at the end, including empty input.
- Do not modify the input. The implementation uses only the Python standard
  library and retains type hints. Runtime is O(n); auxiliary space is O(n).
- Public unittest coverage includes empty/plain text, each bracket type,
  adjacent and nested pairs, crossed pairs, unmatched brackets, and mixed text.

## Verification

Run from the task workspace with Python 3.11+:

```sh
python -m unittest discover -v
```

Observed result: passed all 9 tests (`Ran 9 tests`, `OK`), exit code 0.

Additional verification: `python -m py_compile solution.py` passed with exit code 0.
An AST check confirmed at least three unittest test methods, including batch
coverage (exit code 0).
