# Day 2 handoff

## Design decisions

- Keep the public `merge(left: dict[str, int], right: dict[str, int]) -> dict[str, int]` signature and type hints.
- Copy the left dictionary, then add each right count using zero for missing keys. The result contains the union of keys, including zero and negative totals.
- Always return a fresh dictionary. Neither input is mutated, including when both arguments reference the same dictionary. A shallow copy suffices because the declared keys and values are immutable strings and integers.
- Use only Python 3.11+ and the standard library. No ordering guarantee beyond normal dictionary behavior is added.
- Add `merge_many(cases: list[tuple]) -> list`, calling `merge(*case)` for each tuple in case order. An empty batch returns `[]`; exceptions propagate unchanged and stop processing immediately.
- Keep the day-1 `merge` implementation and signature unchanged. Batch processing does not mutate the cases list, its tuples, or their dictionary arguments.

## Verification

Run from the task workspace:

```sh
python -m unittest discover -v
```

The public regression suite covers shared and distinct keys, zero and negative totals, input preservation, result independence, empty inputs, and aliased inputs.

Day-2 coverage adds ordered batch results, empty batches, preservation of cases and arguments, shared arguments across cases, independent results, invalid positional argument counts, and propagation of the identical first exception with no later calls.

Observed result from `python -m unittest discover -v` in the task workspace:

```text
Ran 9 tests in 0.001s

OK
```

The command exited with status 0; all five day-1 methods and all four batch methods passed.
