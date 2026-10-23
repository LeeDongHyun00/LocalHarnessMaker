# Day 2 handoff

## Design decisions

- Preserve the typed public API `inclusive(start: int, stop: int) -> list[int]`.
- Select a step of +1 for ascending or equal endpoints and -1 for descending endpoints.
- Use `range(start, stop + step, step)` to include the final endpoint, then return a fresh list. Equal endpoints yield a singleton.
- Inputs are integers; no input collections are mutated. Validation of other input types is unspecified.
- Use Python 3.11+ and only the standard library.
- Add `inclusive_many(cases: list[tuple]) -> list`, calling `inclusive(*case)` in input order and returning a fresh result list. Empty input returns `[]`.
- Leave the Day 1 implementation unchanged. Batch processing does not mutate cases or their arguments, and the first exception propagates unchanged with no later calls attempted.

## Verification

Run from the workspace root:

```sh
python -m py_compile solution.py
python -m unittest discover -v
```

Public regression coverage includes ascending, descending, equal, negative, and zero-crossing endpoints.

Observed verification in the supplied workspace on 2026-10-23:

- `python -m py_compile solution.py` passed (exit code 0).
- `python -m unittest discover -v` passed all 8 tests (exit code 0; `Ran 8 tests in 0.002s`, `OK`).
- An AST check of `test_solution.py` passed (exit code 0), confirming at least three test methods and batch coverage.

The four batch tests cover ordered mixed cases, empty input, argument identity and non-mutation, and propagation of the exact exception object with processing stopped at the failing case. The four Day 1 regression tests remain passing.
