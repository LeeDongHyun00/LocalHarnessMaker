# Day 1 handoff

## Design decisions

- Preserve the public signature `flatten(items: list[list[int]]) -> list[int]`.
- Use a list comprehension with two loops to flatten exactly one level in
  outer-list and inner-list order. Empty inner lists contribute no elements.
- Allocate a new result list on every call; neither the outer list nor any
  inner list is modified. Elements are copied by reference, without recursive
  flattening or deep copying.
- Use only Python 3.11+ and the standard library.

## Regression coverage

`test_solution.py` covers ordering and duplicates, empty inner lists, empty
inputs, fresh result lists, repeated references to an inner list, input
preservation, and independence of subsequent result/input list mutations.

## Verification

Run from the task workspace:

```sh
python -m unittest discover -v
```

Day 1 result: all 4 unittest test methods passed.

## Day 2 extension

- Added the public API `flatten_many(cases: list[tuple]) -> list`.
- Each tuple is unpacked as positional arguments to `flatten`; results are
  returned in case order. Empty cases produce a fresh empty list.
- Cases and arguments are not mutated. Evaluation stops at the first exception,
  which propagates unchanged. The day-1 `flatten` implementation and signature
  remain unchanged.
- Retained all 4 day-1 tests and added 5 batch tests covering ordering, empty
  batches, shared inputs and mutation independence, exception identity and
  stopping at the first failure, and invalid positional arguments.

Day 2 verification command, run from the task workspace:

```sh
python -m unittest discover -v
```

Observed result: exit code 0; `Ran 9 tests in 0.002s`, followed by `OK`.
All 9 unittest test methods passed, including the 5 batch test methods.
