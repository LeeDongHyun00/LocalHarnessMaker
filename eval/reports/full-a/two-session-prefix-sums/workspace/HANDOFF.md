# Day 1 handoff

Implemented `prefix(items: list[int]) -> list[int]` using Python 3.11+
and the standard library.

## Design decisions

- Use a running total and append each inclusive sum to a fresh list.
- Preserve the public type hints and input order, with one output per input.
- Leave the input list untouched; empty input naturally returns a fresh empty list.
- Use integer addition directly to support positive values, negative values, and zero.
- The implementation takes O(n) time and O(n) output space.

## Verification

Run from the task workspace:

```sh
python -m unittest discover -v
```

The five public API regression tests cover positive values, empty input,
negative values and zero, a singleton, and input preservation with a fresh result.

# Day 2 handoff

Added `prefix_many(cases: list[tuple]) -> list`. Each tuple is unpacked as
positional arguments to the existing `prefix` function. Results follow case
order, and an empty batch returns `[]`. Exceptions propagate directly; the
first failure stops processing before any later case is called. The batch
implementation does not modify cases or their arguments, and the day-1
`prefix` implementation and signature remain unchanged.

Added five batch test methods covering ordered results, empty batches,
preservation of cases and shared arguments, independent result lists,
positional argument forwarding, and propagation of the exact first exception
object with no subsequent calls. Retained all five day-1 regression tests.

## Day 2 verification evidence

Executed from the runner-provided workspace:

```sh
python -m unittest discover -v
```

Observed result: exit code 0; all 10 test methods passed.

```text
Ran 10 tests in 0.001s

OK
```
