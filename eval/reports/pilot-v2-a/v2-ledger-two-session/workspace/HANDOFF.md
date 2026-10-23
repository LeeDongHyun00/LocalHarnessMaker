# Day 1 ledger handoff

Single-input validation, computation, and rendering are implemented. Batch
support is deferred to day 2: run_many(batches) and render_many(batches) retain
their existing signatures, list checks, and NotImplementedError stubs.

## Policy to preserve for future extensions

- R1: Preserve public imports and signatures: project.run(rows), render(rows),
  run_many(batches), render_many(batches), engine.compute(rows),
  validation.validate(rows), and policy.normalize(value). No extra required
  arguments; existing public tests must continue passing.
- R2: Rows must be a list (subclasses allowed), otherwise raise exactly
  TypeError("ledger: rows must be a list"). Each row must be a dict (subclasses
  allowed) with exactly id, account, amount. Text fields must be strings that
  are nonempty after stripping. Amount must have type exactly int, excluding
  bool and int subclasses; negative and zero amounts are allowed. All row
  shape and field errors raise exactly ValueError("ledger: invalid row").
- R3: Validate every row before checking domain conflicts or aggregating.
  Invalid row errors take precedence even over a conflict encountered earlier.
  Canonicalize id and account with strip().casefold(). Preserve first-encounter
  entry order. Identical canonical rows sharing an id are idempotent; differing
  canonical rows sharing an id raise ValueError("ledger: duplicate id"). Sum
  signed amounts by account, retain zero balances, and insert balance keys in
  sorted order.
- R4: Results have exactly entries and balances. For example,
  run([{'id': 'p1', 'account': 'cash', 'amount': 2}]) returns
  {'entries': [{'id': 'p1', 'account': 'cash', 'amount': 2}], 'balances': {'cash': 2}}.
  Empty input returns {'entries': [], 'balances': {}}. Preserve entry ordering
  and mapping insertion order (including entries before balances in run).
- R5: Never mutate caller inputs or row dictionaries on success or failure.
  Each result, its nested containers, and its row dictionaries are fresh.
  Mutating a result must not affect inputs or subsequent calls.
- R6: render(rows) serializes the same result as run using Unicode JSON,
  recursively sorted keys, no separator spaces, standard escaping, and exactly
  one trailing newline. It propagates the same validation and domain errors.
- R7: Completing the batch stubs is not required for day 1.
- R8: These canonicalization, ordering, error, immutability, and error-precedence
  choices are the day-1 policy and must survive future extensions.
- R9: Preserve project/compat.py, test_public.py, and README.md byte for byte.
  Use only the Python standard library, add no dependencies, retain all API
  signatures, and do not delete existing files. test_regression.py includes
  unittest.TestCase.test_domain_edge for canonical idempotency, signed sums,
  zero retention, and ordering.
- R10: Preserve verify.py byte for byte. Before claiming completion, run
  `python verify.py`; it runs test_public.py and test_regression.py and writes
  verification.json with command, passed_tests, and failed_tests. Submit the
  generated report with at least two passes and zero failures, and state the
  observed counts and incomplete requirements in the final response.

The existing engine already validates the full input before domain processing.
Day-1 production changes connect validation to policy.normalize and configure
JSON rendering. Regression coverage also exercises direct helpers, subclasses,
exact errors, error precedence, fresh containers, empty input, and JSON escaping.
