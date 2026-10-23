# Day 1 handoff

Implemented `last_index(items: list[str], target: str) -> int | None`.

## Design decisions

- Scan indices backward and return the first equal item found, which is the
  last zero-based matching index in the original list.
- Use ordinary string equality for case-sensitive matching.
- Return `None` when the scan finds no match, including for an empty list.
- Read the input without modifying it or creating a reversed copy.
- Preserve the public type hints and use only the Python 3.11+ standard library.
- The implementation takes O(n) time in the worst case and O(1) extra space.

## Verification

Run from the task workspace:

```sh
python -m unittest discover -v
```

`test_solution.py` includes six unittest methods covering duplicates, absent
targets, empty input, case sensitivity, boundary indices, and input preservation.

# Day 2 handoff

Added `last_index_many(cases: list[tuple]) -> list` while preserving the
day-1 `last_index` implementation and signature.

- Each tuple is unpacked as positional arguments to `last_index`.
- Results retain case order; an empty batch returns `[]`.
- Exceptions propagate unchanged and stop processing before later cases.
- The wrapper does not modify the cases list, tuples, or arguments.

Added five batch unittest methods covering ordered results, empty batches,
preservation of cases and shared arguments, exception identity and stopping at
the first failure, and invalid positional arguments. All six day-1 tests remain.

## Day 2 verification evidence

Executed from the task workspace:

```sh
python -m unittest discover -v
```

Observed result: exit code 0; `Ran 11 tests in 0.001s`, followed by `OK`.
All eleven test methods passed, including the five batch methods.
