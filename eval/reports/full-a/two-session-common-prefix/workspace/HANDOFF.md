# Day 2 handoff

Implemented `common(items: list[str]) -> str` in `solution.py`.

## Design decisions

- Preserve the supplied public signature and type hints.
- Start with the first string, then shorten the candidate prefix by comparing
  characters against each remaining string. Stop once the prefix is empty.
- Use Python string equality directly: matching is case-sensitive and compares
  Unicode characters without normalization or case folding.
- Return an empty string for empty input; a single item is returned unchanged.
- Only read the input list and create local strings; never mutate the collection.
- Use Python 3.11+ and the standard library, with no extra dependencies.

## Regression coverage and verification

`test_solution.py` exercises empty input, one item, shared prefixes, shortest and
identical strings, mismatches, case sensitivity, empty strings, Unicode, and
input preservation through the public API.

Run from the task workspace:

```sh
python -m unittest discover -v
```

## Day 2 batch API

Added `common_many(cases: list[tuple]) -> list` in `solution.py`. Each tuple
is unpacked as positional arguments to `common`, and results retain case order.
Empty cases return `[]`. Calls run sequentially; the first exception propagates
unchanged and prevents later calls. The implementation only reads cases and
their arguments. The day-1 `common` implementation and signature are unchanged.

Added four unittest methods covering empty batches, ordered results, Unicode,
shared arguments and input preservation, invalid argument counts, and exception
identity with no calls after the first failure. All eight day-1 tests remain.

Verification run from the runner-provided workspace:

```sh
python -m unittest discover -v
```

Observed result: exit code 0, `Ran 12 tests in 0.001s`, `OK`.
