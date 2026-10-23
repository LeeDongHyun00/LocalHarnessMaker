# Day 2 handoff

## design decisions

- Keep the existing public API and type hints:
  `merge(left: dict[str, int], right: dict[str, int]) -> dict[str, int]`.
- Copy the left dictionary, then add every right-hand count using zero for
  missing keys. This returns the union of keys and preserves zero and negative
  totals without mutating either input, including when both inputs are the same
  dictionary.
- Return a fresh dictionary even for empty inputs. Integer values require no
  deep copy.
- Use only the Python 3.11+ standard library. Regression coverage exercises
  shared and distinct keys, zero and negative totals, input preservation,
  result independence, empty inputs, and aliased inputs.
- Add `merge_many(cases: list[tuple]) -> list` using ordered calls to
  `merge(*case)`. Empty batches return `[]`; the first exception propagates
  unchanged and prevents later calls. Cases and argument dictionaries are not
  mutated. The day-1 `merge` implementation and signature remain unchanged.
- Batch tests cover result order, empty batches, input preservation, aliased
  arguments, independent results, exception identity, and stopping on failure.

## Verification

Run from the task workspace root:

```sh
python -m unittest discover -v
```

Observed result: exit 0; all 8 tests passed (`Ran 8 tests in 0.002s`, `OK`).
