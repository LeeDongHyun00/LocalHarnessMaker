# Day 2 handoff

## Design decisions

- Retained the supplied public API, `common(items: list[str]) -> str`.
- Start with the first string and shorten a local prefix to match each subsequent
  string. Stop when the prefix becomes empty.
- Compare Python characters directly, preserving case-sensitive Unicode behavior
  without normalization or case folding.
- Empty input returns `""`; a single item returns that item. The implementation
  only reads the input list and does not mutate it.
- Use Python 3.11+ and only the standard library. Public unittest coverage includes
  empty input, single items, shared prefixes, case sensitivity, empty strings,
  Unicode, and input preservation.

## Verification

Run from the workspace root:

```sh
python -m unittest discover -v
```

Observed result after the Day 2 implementation: exit code 0;
`Ran 11 tests in 0.002s`, followed by `OK`.

## Day 2 changes

- Preserved `common(items: list[str]) -> str` without changes.
- Added `common_many(cases: list[tuple]) -> list`, calling `common(*case)`
  sequentially and collecting results in case order. Empty cases return `[]`.
- The wrapper only reads cases and their arguments. Exceptions are not caught,
  so the first exception propagates unchanged and later cases are not called.
- Retained all seven Day 1 tests and added four batch tests covering ordered
  results, input preservation, empty batches, positional argument forwarding,
  and exception identity with immediate termination.
