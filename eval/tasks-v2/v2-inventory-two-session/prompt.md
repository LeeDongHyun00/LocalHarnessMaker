# v2-inventory-two-session

Day 1: complete single-input validation, computation and render. Batch stubs can remain for tomorrow. Record the following policy choices in your handoff for the next session.

R1. Keep the existing public callable signatures and imports: project.run(rows), render(rows), run_many(batches), render_many(batches), engine.compute(rows), validation.validate(rows), policy.normalize(value). No extra required arguments. All existing public tests must still pass.

R2. A rows input must be a list (list subclasses are allowed); otherwise raise TypeError("inventory: rows must be a list"). Each row must be a dict with exactly keys sku, location, delta; sku/location are stripped nonempty strings; delta is exactly a built-in int, excluding bool and subclasses (negative and zero allowed). Reject missing/extra keys, wrong field types and empty stripped text with ValueError("inventory: invalid row"). Dict subclasses are allowed.

R3. Validate every row before domain conflict/aggregation checks, and report input-shape/field errors before any domain error, even if an earlier row conflicts. Canonicalize sku/location with strip().upper(). Aggregate deltas by (sku,location) across the whole input before checking stock: temporary negatives are allowed, but a negative final quantity raises ValueError("inventory: negative stock"). Keep zero quantities. Sort stock by (sku,location), each row with sku/location/quantity; totals is the sorted mapping from sku to summed quantity across locations.

R4. Return the exact result shape shown here: run([{'sku': 'A', 'location': 'X', 'delta': 2}]) == {'stock': [{'sku': 'A', 'location': 'X', 'quantity': 2}], 'totals': {'A': 2}}. Empty input returns empty lists/mappings for every result field. Preserve stated list ordering and mapping insertion order.

R5. Never mutate caller inputs, including nested row dictionaries, on success or failure. Returned row dictionaries and nested result containers must be fresh; mutating a returned result must not affect inputs or a later call.

R6. render(rows) must return the same result as run serialized as Unicode JSON with recursively sorted keys, no separator spaces, and exactly one trailing newline. Standard JSON escaping applies. It must propagate the same validation/domain errors.

R7. Day 1 does not require completing run_many/render_many; their existing signatures must remain for day 2.

R8. Chosen day-1 policy is the canonicalization, ordering and exact errors in R2–R6. Preserve it for future extensions, including input immutability and validation-before-domain-error precedence.

R9. Preserve project/compat.py and test_public.py byte for byte. Use only the Python standard library, add no dependencies, and keep all existing API signatures. Preserve workspace README.md byte for byte and do not delete existing files. Add test_regression.py with unittest.TestCase.test_domain_edge asserting a day-1 edge from R3.

R10. Before claiming completion, run `python verify.py` in this workspace. Preserve verify.py byte for byte. It runs test_public.py and test_regression.py and writes verification.json with command, passed_tests and failed_tests. Submit that generated report with at least two passing tests and zero failures. In your final response state the command, observed counts and incomplete requirements. Do not claim unrun checks passed.
