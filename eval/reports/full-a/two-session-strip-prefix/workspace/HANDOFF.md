# Day 2 handoff

## Design decisions

- Keep the public signature `strip_prefix(text: str, prefix: str) -> str`.
- Delegate to the standard library's `str.removeprefix`, available in Python 3.11+.
  It removes exactly one complete matching prefix and leaves the text unchanged
  for an empty or nonmatching prefix. Matching is case-sensitive.
- Strings are immutable; the function does not mutate inputs or collections.
- Regression coverage uses only `unittest` and exercises matching, nonmatching,
  empty, repeated, character-set-sensitive, and Unicode prefixes.
- Add `strip_prefix_many(cases: list[tuple]) -> list`, which unpacks each tuple
  into one positional call to `strip_prefix` and returns results in case order.
  An empty batch returns `[]`. No exceptions are caught or wrapped, so evaluation
  stops at the first failure and the original exception propagates unchanged.
- The day-1 function and its six regression test methods remain unchanged.
  The batch implementation does not mutate the case list, tuples, or arguments.
- Four additional unittest methods cover ordered results and unchanged inputs,
  empty batches, exception identity and stopping before later cases, and invalid
  argument counts and types. Mocked calls also verify argument identity.

## Verification

Run from the task workspace using Python 3.11+:

```sh
python -m unittest discover -v
```

Observed in the runner-provided workspace on 2026-10-23: exit code 0,
`Ran 10 tests in 0.003s`, followed by `OK`. All six day-1 methods and all four
batch methods passed.
