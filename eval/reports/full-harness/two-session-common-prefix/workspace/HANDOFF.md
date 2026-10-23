# Day 2 handoff

## design decisions

- Preserve the public API `common(items: list[str]) -> str`.
- Add `common_many(cases: list[tuple]) -> list`, calling `common(*case)`
  once per tuple in input order. Return `[]` for no cases and let the first
  exception propagate unchanged, without processing later cases.
- The batch wrapper does not mutate cases or their arguments.
- Start with the first string and shorten a local prefix using case-sensitive
  character comparisons against each remaining string.
- Return `""` for empty input and the sole string for a single item.
- Read inputs without modifying the collection or its strings. Compare Unicode
  characters directly without normalization or case folding.
- Use Python 3.11+ and only the standard library; no complexity constraint is
  imposed.
- Public unittest coverage checks empty and single inputs, shared and absent
  prefixes, case sensitivity, empty strings, identical strings, Unicode, and
  preservation of the input list.
- Batch coverage checks ordered results, empty batches, argument forwarding,
  input preservation, and exception identity with processing stopped on failure.

## Verification

Run from the task workspace:

```sh
python -m py_compile solution.py test_solution.py
python -m unittest discover -v
```

Observed results after the Day 2 changes:

- `python -m py_compile solution.py test_solution.py`: exit code 0; passed.
- `python -m unittest discover -v`: exit code 0; ran 12 tests in 0.002s,
  all passed (`OK`).
