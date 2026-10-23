# Day 1 handoff

Implemented `common(items: list[str]) -> str` in `solution.py`.

## Design decisions

- Start with the first string and shorten the candidate prefix by comparing
  characters against each subsequent string. Stop when the prefix becomes empty.
- Return an empty string for empty input and preserve the sole string for a
  single-item input.
- Use Python's case-sensitive character comparison without normalization or
  case folding; Unicode characters are supported by ordinary string operations.
- Preserve the existing type hints and leave the input list unchanged.
- Use only the standard library, with Python 3.11+ as the target runtime.

## Verification

Run from the task workspace:

```sh
python -m unittest discover -v
```

`test_solution.py` covers empty and single-item inputs, shared and absent
prefixes, empty strings, identical strings, case sensitivity, Unicode, and input
preservation.

Day 1 verification result: all 7 unittest methods passed with the command above.

## Day 2 extension

Added `common_many(cases: list[tuple]) -> list` in `solution.py`. Each tuple
is unpacked into positional arguments for `common`, with results returned in
case order. Empty input returns `[]`. Calls run sequentially, so the first
exception propagates unchanged and later cases are not called. The wrapper
does not modify cases or their arguments. The day-1 `common` implementation
and signature remain unchanged.

Added six batch unittest methods in `test_solution.py`, covering empty input,
ordered results, input preservation (including shared argument lists), positional
argument forwarding, exception identity and stopping at the first failure, and
invalid call arity. All seven day-1 regression methods remain.

Day 2 verification command, run from the task workspace:

```sh
python -m unittest discover -v
```

Observed result: exit code 0; `Ran 13 tests in 0.003s`, followed by `OK`.
All 13 unittest methods passed.
