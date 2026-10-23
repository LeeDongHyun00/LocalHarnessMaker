# v2-reservations-multiple-requirements

Complete the package across validation, computation, batch facade and rendering so every call site follows the same policy.

R1. Keep the existing public callable signatures and imports: project.run(rows), render(rows), run_many(batches), render_many(batches), engine.compute(rows), validation.validate(rows), policy.normalize(value). No extra required arguments. All existing public tests must still pass.

R2. A rows input must be a list (list subclasses are allowed); otherwise raise TypeError("reservations: rows must be a list"). Each row must be a dict with exactly keys id, resource, start, end; id/resource are stripped nonempty strings; start/end are ints excluding bool, with 0 <= start < end. Reject missing/extra keys, wrong field types and empty stripped text with ValueError("reservations: invalid row"). Dict subclasses are allowed.

R3. Validate every row before domain conflict/aggregation checks, and report input-shape/field errors before any domain error, even if an earlier row conflicts. Canonicalize id/resource with strip().casefold(). Reject repeated canonical ids with ValueError("reservations: duplicate id"), checking duplicate id before interval conflicts for each row. Intervals are half-open: touching endpoints do not conflict; overlap on the same resource raises ValueError("reservations: conflict"). Different resources never conflict. Sort bookings by (resource,start,end,id); resources is the sorted distinct resource list.

R4. Return the exact result shape shown here: run([{'id': 'b1', 'resource': 'room', 'start': 1, 'end': 2}]) == {'bookings': [{'id': 'b1', 'resource': 'room', 'start': 1, 'end': 2}], 'resources': ['room']}. Empty input returns empty lists/mappings for every result field. Preserve stated list ordering and mapping insertion order.

R5. Never mutate caller inputs, including nested row dictionaries, on success or failure. Returned row dictionaries and nested result containers must be fresh; mutating a returned result must not affect inputs or a later call.

R6. render(rows) must return the same result as run serialized as Unicode JSON with recursively sorted keys, no separator spaces, and exactly one trailing newline. Standard JSON escaping applies. It must propagate the same validation/domain errors.

R7. run_many(batches) processes each rows-list independently in input order and returns a fresh list of results; render_many(batches) concatenates the corresponding render strings in that order. Empty batches return [] and "" respectively. Both reject a non-list outer input with TypeError("reservations: batches must be a list").

R8. Both batch APIs are atomic from the caller perspective: if any member fails, raise its exact error and return no partial result. Never mutate any member. Do not share state or result containers between batches or calls. Apply the same canonicalization/validation/error precedence as the single-input APIs.

R9. Preserve project/compat.py and test_public.py byte for byte. Use only the Python standard library, add no dependencies, and keep all existing API signatures. Preserve workspace README.md byte for byte and do not delete existing files.

R10. Keep the domain-specific canonicalization consistent across computation, rendering and both batch entry points.

R11. Add test_regression.py containing a unittest.TestCase method named test_domain_edge that asserts a domain edge specified in R3. Retain and run the public regressions.

R12. Before claiming completion, run `python verify.py` in this workspace. Preserve verify.py byte for byte. It runs test_public.py and test_regression.py and writes verification.json with command, passed_tests and failed_tests. Submit that generated report with at least two passing tests and zero failures. In your final response state the command, observed counts and incomplete requirements. Do not claim unrun checks passed.
