# Reservations: day 1 handoff

Single-input validation, computation and rendering are complete. Day 2 remains:
implement `run_many(batches)` and `render_many(batches)`; the existing stubs and
their list checks remain in place.

Preserve the public signatures/imports: `project.run(rows)`, `render(rows)`,
`run_many(batches)`, `render_many(batches)`, `engine.compute(rows)`,
`validation.validate(rows)` and `policy.normalize(value)`. No required arguments
may be added. Use only the Python standard library.

The chosen day-1 policy must carry forward to batch and other extensions:

- Rows must be a list, including subclasses; otherwise raise
  `TypeError("reservations: rows must be a list")`.
- Each row must be a dict (subclasses allowed) with exactly `id`, `resource`,
  `start`, `end`. Text fields must be strings with nonempty stripped text.
  Times must be integers, excluding bool, with `0 <= start < end`.
  Every shape/field violation raises `ValueError("reservations: invalid row")`.
- Validate every row before any domain check, so any invalid row takes precedence
  over an earlier duplicate or conflict. Return fresh canonical rows from validate.
  Canonicalize both text fields using `strip().casefold()`.
- Process domain checks in input order. For each row, check canonical id duplication
  before checking overlaps: `ValueError("reservations: duplicate id")` or
  `ValueError("reservations: conflict")`. An earlier row's conflict still precedes
  a later row's duplicate id. Intervals are half-open; touching endpoints are valid.
  Overlaps conflict only on the same canonical resource.
- Return exactly `{'bookings': [...], 'resources': [...]}` in that mapping order.
  Sort bookings by `(resource, start, end, id)` and resources as sorted distinct
  canonical strings. Booking key insertion order follows the input row's key order.
  Empty input yields `{'bookings': [], 'resources': []}`.
- Never mutate inputs on success or failure. Returned row dictionaries and all
  result containers are fresh; editing one result must not affect later calls.
- Render the run result as Unicode JSON (`ensure_ascii=False`), recursively sorted
  keys, compact separators, standard escaping and exactly one trailing newline.
  Propagate the same validation and domain errors.

Preserve README.md, project/compat.py, test_public.py and verify.py byte for byte.
Do not delete existing files. Regression coverage includes the required
`unittest.TestCase.test_domain_edge` for canonical same-resource touching intervals.
Run `python verify.py` before completion; submit the generated verification.json
with at least two passing tests and zero failures. Report observed counts and
remaining requirements in the final response.
