# Inventory day-1 handoff

Day 1 implements single-input validation, computation, and rendering. Day 2 still
needs batch behavior in `run_many(batches)` and `render_many(batches)`; their
existing list checks and `NotImplementedError('batch support')` stubs remain.

## Policies to preserve (R1–R9)

- Keep public imports and signatures: `project.run(rows)`, `render(rows)`,
  `run_many(batches)`, `render_many(batches)`, `engine.compute(rows)`,
  `validation.validate(rows)`, and `policy.normalize(value)`. No new required
  arguments or dependencies; use only the Python standard library.
- Rows must be a list (subclasses allowed), otherwise raise
  `TypeError("inventory: rows must be a list")`. Every row must be a dict
  (subclasses allowed) with exactly `sku`, `location`, and `delta`. Text fields
  must be strings with nonempty stripped values. Delta must have exactly type
  `int`, excluding bool and int subclasses; zero and negative values are valid.
  All row violations raise `ValueError("inventory: invalid row")`.
- Validate all rows before domain checks, so malformed later rows take precedence
  over earlier stock conflicts. Canonicalize sku/location using `strip().upper()`
  on fresh dictionaries. Never mutate caller inputs, on success or failure.
- Aggregate all deltas by canonical `(sku, location)` before checking stock.
  Temporary negatives are allowed; any negative final quantity raises
  `ValueError("inventory: negative stock")`. Keep zero quantities.
- Return exactly `{'stock': [{'sku': ..., 'location': ..., 'quantity': ...}],
  'totals': {...}}`. Sort stock by `(sku, location)` and insert totals in sorted
  sku order, summing across locations. Empty input yields `{'stock': [],
  'totals': {}}`. Every call returns fresh nested containers and row dictionaries.
- Render the same result as Unicode JSON (`ensure_ascii=False`), recursively
  sorted keys, compact separators, standard JSON escaping, and exactly one
  trailing newline. Propagate validation and domain errors unchanged.
- Preserve these day-1 choices for all future extensions, especially error
  precedence, ordering, and input/result isolation. Keep README.md,
  project/compat.py, test_public.py, and verify.py byte for byte; do not delete
  existing files.

## Verification (R10)

Run `python verify.py` before claiming completion. It runs the public and
regression suites and generates `verification.json` with the command and observed
passing/failing test counts. Submit that generated report with at least two
passing tests and zero failures. `test_regression.py` includes
`unittest.TestCase.test_domain_edge` for temporary negative stock resolving to
zero after canonical aggregation.
