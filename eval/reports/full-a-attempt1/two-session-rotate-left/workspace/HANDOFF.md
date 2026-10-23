# Day 1 handoff

Implemented `rotate` in `solution.py` and public regression tests in
`test_solution.py`, using only the Python standard library.

## Design decisions

- Preserve the public `list[int]` input/output and `int` steps type hints.
- Return a fresh empty list before computing modulo, avoiding division by zero.
- Normalize steps with `steps % len(items)`. Positive values rotate left;
  Python's modulo behavior also handles negative values as right rotations.
- Concatenate two slices to produce a fresh list without mutating the input,
  including for zero steps and full rotations. This uses O(n) time and space.
- Cover positive and negative wraparound, empty input, zero and full rotations,
  single-element input, and input/result independence with unittest.

## Verification

From the task workspace with Python 3.11+:

```sh
python -m unittest discover -v
```

Day 1 result: all 6 test methods passed on Python 3.13.5.

## Day 2 extension

Added `rotate_many(cases: list[tuple]) -> list` in `solution.py`. Each tuple
is unpacked into positional arguments for `rotate`, and results are collected
in case order. An empty batch returns a fresh empty list. Exceptions propagate
unchanged and stop processing immediately. The existing `rotate` implementation
and all six Day 1 regression tests remain unchanged.

The batch implementation does not mutate cases or their arguments. Five new
unittest methods cover result order, empty batches, input and result independence,
the identity of the first propagated exception and stopping subsequent calls,
and invalid positional arguments.

Day 2 verification command, run from the task workspace:

```sh
python -m unittest discover -v
```

Observed result: `Ran 11 tests in 0.002s`, followed by `OK` (exit code 0).
All six Day 1 methods and all five batch methods passed.
