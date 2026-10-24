# Day 1 inventory handoff

Day 1 implements single-input validation, computation and rendering using only
the Python standard library. Existing public signatures and imports remain:
`project.run(rows)`, `render(rows)`, `run_many(batches)`, `render_many(batches)`,
`engine.compute(rows)`, `validation.validate(rows)`, and `policy.normalize(value)`.
No additional required arguments or dependencies were added.

## Policy to preserve in day 2

- Rows must be a list; list subclasses are accepted. Other inputs raise
  `TypeError("inventory: rows must be a list")`.
- Every row must be a dict (subclasses accepted) with exactly `sku`, `location`,
  and `delta`. Text fields must be strings with nonempty stripped values.
  Delta must have exactly built-in type `int`; bool and int subclasses are
  rejected. Negative and zero deltas are allowed. All invalid rows raise
  `ValueError("inventory: invalid row")`.
- Canonicalize sku and location with `strip().upper()`.
- Validate all rows before any domain conflict or aggregation check. Invalid
  input takes precedence over domain errors, even after an earlier negative row.
- Aggregate the entire input by canonical `(sku, location)` before checking
  stock. Temporary negatives are allowed; any final negative quantity raises
  `ValueError("inventory: negative stock")`. Retain zero quantities.
- Results have exactly `stock` and `totals`. Stock is sorted by `(sku, location)`
  and contains dictionaries with `sku`, `location`, `quantity`. Totals maps sku
  to the sum across locations, with keys inserted in sorted order. Empty input
  returns `{'stock': [], 'totals': {}}`.
- Never mutate caller lists or row dictionaries, on success or failure. Return
  fresh row dictionaries and nested containers on every call, including empty
  results. Mutating results must not affect inputs or later calls.
- Render the run result as Unicode JSON (`ensure_ascii=False`), recursively
  sorted keys, compact separators, standard JSON escaping, and exactly one
  trailing newline. Propagate the same validation and domain errors.

## Remaining work

Day 2 must implement `run_many(batches)` and `render_many(batches)`. Their existing
signatures and current stubs remain. Extend the day 1 policy above, including
input immutability and validation-before-domain-error precedence.

Preserve `README.md`, `project/compat.py`, `test_public.py`, and `verify.py` byte
for byte. Do not delete existing files. Keep public tests passing and use only
the standard library.

## Verification

Run `python verify.py`; it runs `test_public.py` and `test_regression.py` and
generates `verification.json` with the command and passing/failing test counts.
The regression suite includes `unittest.TestCase.test_domain_edge` for temporary
negative stock, canonical aggregation, zero retention, ordering, and totals.
