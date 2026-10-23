# Day 1 handoff

## Design decisions

- Preserve the public `interleave(left: list[int], right: list[int]) -> list[int]` signature.
- Build a fresh result list, appending each shared position left first, then right.
- Append the remaining slices in order. At most one slice is nonempty, which also handles empty inputs naturally.
- Read inputs without modifying them; passing the same list twice is supported.
- Use only the standard library and Python 3.11+ compatible syntax.

## Regression coverage and verification

`test_solution.py` contains six unittest methods covering equal lengths, both longer-input cases, empty inputs, input preservation/result independence, and aliased inputs with repeated and negative values.

Run from the task workspace:

```sh
python -m unittest discover -v
```

Day 1 verification: the command above passed all six tests.

## Day 2 extension

- Added public `interleave_many(cases: list[tuple]) -> list` in `solution.py`.
- Each tuple is unpacked as positional arguments to `interleave`, in case order; an empty batch returns `[]`.
- Exceptions propagate directly without wrapping, and processing stops at the first exception.
- The batch implementation reads cases and arguments without modifying them. The day-1 `interleave` signature and implementation are unchanged.
- Retained all six day-1 unittest methods and added five batch methods covering ordered results, empty batches, preservation of cases and aliased arguments, independent results, exception identity and stopping behavior, and invalid argument counts.

Day 2 verification command, run from the task workspace:

```sh
python -m unittest discover -v
```

Observed result: exit code 0; `Ran 11 tests in 0.002s`, followed by `OK`. All six day-1 tests and all five batch tests passed.
