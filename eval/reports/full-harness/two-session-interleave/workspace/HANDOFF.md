# Day 2 handoff

## Day 2 changes

- Added `interleave_many(cases: list[tuple]) -> list`, calling `interleave(*case)` for each case in order. Empty cases return `[]`.
- The first exception propagates unchanged and later cases are not evaluated.
- The existing `interleave` API and implementation are unchanged. Cases and argument collections are not mutated; iterator arguments retain the existing consumption behavior.
- Added five batch unittest methods covering ordered results, empty cases, input preservation and independent result lists, exception identity and stopping, and positional argument errors. All six Day 1 tests remain.

## Design decisions

- `interleave` accepts two finite iterable inputs and returns a new list, with generic type hints supporting different item types.
- Consume one left item, then one right item. Once either iterator ends, append the other iterator's remainder in order.
- Use iterator exhaustion rather than a sentinel value, so every input value, including `None`, is preserved.
- Input collections are not mutated; iterator inputs are consumed. Items are retained by reference rather than copied.
- The implementation uses Python 3.11-compatible standard library features. Runtime and output storage are linear in the total number of items.
- Six unittest methods cover equal lengths, both longer-input cases, empty inputs, input preservation/new result allocation, and mixed iterable/item types.

## Verification

Run from the workspace root:

```sh
python -m unittest discover -v
```

Observed after the Day 2 implementation: 11 tests ran in 0.001s; `OK` (all passed), exit code 0.
