# Day 1 handoff

Single-input validation, computation, and rendering are complete. Day 2 work
remains: implement `run_many(batches)` and `render_many(batches)`; both retain
their existing signatures and batch stubs.

## Policy to preserve for future extensions

- Keep public imports and callable signatures: `project.run(rows)`,
  `render(rows)`, `run_many(batches)`, `render_many(batches)`,
  `engine.compute(rows)`, `validation.validate(rows)`, and
  `policy.normalize(value)`. Add no required arguments or dependencies.
- Rows must be a list; subclasses are accepted. Otherwise raise exactly
  `TypeError("ledger: rows must be a list")`.
- Every row must be a dict (subclasses accepted) with exactly `id`, `account`,
  and `amount`. Text fields must be strings nonempty after stripping; amount
  must have exactly built-in `int` type, excluding bool and int subclasses.
  Signed amounts and zero are allowed. Any row shape or field error raises
  exactly `ValueError("ledger: invalid row")`.
- Validate all rows before checking domain conflicts or aggregating. A later
  invalid row takes precedence over an earlier conflicting ID.
- Canonicalize IDs and accounts with `strip().casefold()`. Preserve the order
  of first encounters. Repeated identical canonical rows are idempotent;
  conflicting rows sharing a canonical ID raise exactly
  `ValueError("ledger: duplicate id")`.
- Return exactly `{'entries': [...], 'balances': {...}}`. Entries are canonical
  rows in first-encounter order. Sum accepted signed amounts by account, keep
  zero balances, and insert balance keys in sorted order. Empty input produces
  `{'entries': [], 'balances': {}}`.
- Never mutate caller inputs on success or failure. Return fresh row dicts and
  nested result containers, independent of inputs and subsequent calls.
- Render the same result as Unicode JSON (`ensure_ascii=False`), recursively
  sorted keys, compact separators, standard JSON escaping, and exactly one
  trailing newline. Propagate the same validation and domain errors.
- Preserve `project/compat.py`, `test_public.py`, `README.md`, and `verify.py`
  byte for byte. Do not delete existing files. Use only the standard library.

## Verification

Run `python verify.py` from the workspace. It runs public and regression tests
and generates `verification.json` with command, passed_tests, and failed_tests.
The regression suite includes `unittest.TestCase.test_domain_edge`, covering
canonical idempotency, encounter order, signed aggregation, and zero retention.
The generated report accompanies this handoff; consult it for observed counts.
