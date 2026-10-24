# Day 1 routing handoff

Single-input validation, computation, and rendering are complete. Day 2 work is
`run_many(batches)` and `render_many(batches)`; their existing stubs and signatures
remain in place.

Preserve these public callables and imports with no extra required arguments:
`project.run(rows)`, `render(rows)`, `run_many(batches)`, `render_many(batches)`,
`engine.compute(rows)`, `validation.validate(rows)`, and `policy.normalize(value)`.
Use only the Python standard library. Keep existing public tests passing.

## Policy to preserve for future extensions

- Rows must be a list, allowing list subclasses. Otherwise raise exactly
  `TypeError("routing: rows must be a list")`.
- Each row must be a dict, allowing dict subclasses, with exactly `path`,
  `target`, and `priority`. Path and target must be strings whose stripped text
  is nonempty. Priority must have `type(value) is int`: bool and int subclasses
  are invalid; zero and negative integers are valid. Every row violation raises
  exactly `ValueError("routing: invalid row")`.
- Validate every row before canonicalization and domain conflict/aggregation
  processing. Shape and field errors take precedence over any domain error,
  including when an earlier row collides with another path.
- `policy.normalize(value)` canonicalizes paths using `strip().casefold()`,
  collapsing repeated slashes, ensuring one leading slash and removing trailing
  slashes except for root `/`. Targets use only `strip().casefold()`.
- For repeated canonical paths retain the greatest priority, keeping the first
  encounter on ties. Collisions are resolved by this selection rule. Sort rules
  by descending priority, descending canonical path length, then ascending path.
  Targets are sorted distinct targets of retained rules only.
- Return exactly `{'rules': [{'path': '/a', 'target': 'svc', 'priority': 1}],
  'targets': ['svc']}` for the corresponding single-row example. The result's
  mapping order is `rules`, `targets`; row mapping order is `path`, `target`,
  `priority`. Empty input returns `{'rules': [], 'targets': []}`. Preserve all
  specified list and mapping ordering.
- Never mutate caller input, including row dictionaries, on success or failure.
  Return fresh row dictionaries and result containers, independent of inputs
  and later calls.
- Render the same computed result with Unicode JSON, recursively sorted keys,
  compact separators, standard JSON escaping, and exactly one trailing newline.
  Propagate the same validation/domain errors as run.

Keep `README.md`, `project/compat.py`, `test_public.py`, and `verify.py` byte for
byte; do not delete existing files or add dependencies. Regression coverage is
in `test_regression.py`, including `RegressionTests.test_domain_edge` for
canonical collisions, greatest-priority selection, first-on-tie behavior, and root.

Run `python verify.py` before claiming completion. It runs the public and
regression tests and generates `verification.json` with the command and observed
pass/failure counts. Submit that generated report; at least two tests must pass
and none fail. Batch implementation remains intentionally incomplete for day 2.
