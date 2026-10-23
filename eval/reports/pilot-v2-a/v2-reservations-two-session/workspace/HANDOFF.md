# Day 1 reservations policy and day 2 handoff

Day 1 completes single-input validation, computation and rendering. Day 2 still
needs to implement `run_many(batches)` and `render_many(batches)`; both keep their
existing list check and `NotImplementedError('batch support')` stubs.

Preserve all public signatures and imports: `project.run(rows)`, `render(rows)`,
`run_many(batches)`, `render_many(batches)`, `engine.compute(rows)`,
`validation.validate(rows)` and `policy.normalize(value)`. No extra required
arguments or dependencies; use the Python standard library only.

The chosen policy for all future extensions is:

- Rows must be a list, including subclasses; otherwise raise
  `TypeError('reservations: rows must be a list')`.
- Every row must be a dict (subclasses allowed) with exactly `id`, `resource`,
  `start`, `end`. Text fields must be strings with nonempty stripped contents.
  Endpoints must be integers excluding bool, with `0 <= start < end`. Reject all
  shape and field violations with `ValueError('reservations: invalid row')`.
- Validate every row before any domain checks. Canonicalize both text fields
  using `strip().casefold()`. Process domain checks in input order: check each
  row's canonical id for duplication before checking that row for conflicts.
  Raise `ValueError('reservations: duplicate id')` or
  `ValueError('reservations: conflict')` respectively. This does not give a later
  duplicate precedence over an earlier conflict. All field errors take precedence
  over all domain errors.
- Intervals are half-open; touching endpoints are allowed. Overlap only conflicts
  on the same canonical resource. Different resources never conflict.
- Return exactly `{'bookings': [...], 'resources': [...]}`, inserting those keys in
  that order. Bookings contain exactly `id`, `resource`, `start`, `end` and sort by
  `(resource, start, end, id)`. Resources are sorted and distinct. Empty input
  produces `{'bookings': [], 'resources': []}`. Preserve stated list and mapping
  insertion ordering.
- Never mutate caller inputs on success or failure. Return fresh row dictionaries
  and result containers, isolated from inputs and subsequent calls.
- Render the computation result with Unicode JSON, recursively sorted keys,
  compact separators, standard JSON escaping, and exactly one trailing newline.
  Propagate the same validation and domain errors.

Keep `README.md`, `project/compat.py`, `test_public.py`, and `verify.py` byte for
byte; do not delete existing files. `test_regression.py` includes
`unittest.TestCase.test_domain_edge` coverage of touching canonical resources.
Run `python verify.py` before claiming completion; its generated
`verification.json` records the command and observed passing/failing counts.
