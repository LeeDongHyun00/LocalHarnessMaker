# Day 2 handoff

Implementation and design decisions:

- Preserve the existing `windows(items: list[int], size: int) -> list[list[int]]` API.
- Validate nonpositive sizes before processing, including for empty inputs.
- Slice at successive starting positions to produce overlapping windows of exactly
  the requested size. An oversized window produces an empty list naturally.
- Each slice is a fresh list, so input is not mutated and returned windows can be
  changed independently. No dependencies beyond the Python standard library.
- Public unittest coverage includes overlapping windows, size one, exact length,
  oversized windows, empty input, nonpositive sizes, and input preservation.
- Added `windows_many(cases: list[tuple]) -> list`, calling `windows(*case)`
  sequentially and collecting results in case order. Empty cases return `[]`.
  Exceptions propagate unchanged and stop processing immediately; cases and
  their arguments are not mutated.
- Added five batch test methods covering result order, empty batches, input
  preservation and result independence, exception identity and stopping at the
  first failure, and delegation of size and positional-argument validation.

Verification command (run from the workspace root with Python 3.11+):

```sh
python -m unittest discover -v
```

Observed result: all 12 tests passed (`Ran 12 tests in 0.003s`, `OK`), exit code 0.
