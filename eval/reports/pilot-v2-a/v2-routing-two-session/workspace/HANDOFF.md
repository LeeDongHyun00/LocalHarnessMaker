# Day 1 routing policy

Single-input validation, computation and rendering are implemented. Preserve all
public imports and signatures: project.run(rows), render(rows), run_many(batches),
render_many(batches), engine.compute(rows), validation.validate(rows), and
policy.normalize(value). No additional required arguments or dependencies.

Rows must be a list (subclasses accepted), otherwise raise
TypeError("routing: rows must be a list"). Each row must be a dict (subclasses
accepted) with exactly path, target and priority. Path and target must be strings
with nonempty stripped content. Priority must have type exactly int: exclude bool
and int subclasses, accept zero and negatives. Every invalid row raises
ValueError("routing: invalid row"). Validate all rows before canonicalization and
domain aggregation; field/shape errors take precedence over any domain errors.

Paths use strip().casefold(), collapse repeated slashes, have one leading slash,
and have no trailing slash except root /. policy.normalize implements this path
policy. Targets use only strip().casefold(). Repeated canonical paths retain the
greatest priority; first encounter wins ties, including differing targets. No
additional domain conflict errors are specified for day 1. Sort retained rules by
descending priority, descending canonical path length, then ascending path.
Targets are sorted distinct targets from retained rules only.

The exact result is {'rules': [{'path': '/a', 'target': 'svc', 'priority': 1}],
'targets': ['svc']} for that single rule. Empty input returns {'rules': [],
'targets': []}. Preserve list order and mapping insertion order (rules then
targets; path, target, priority in row mappings). Inputs must remain unchanged on
success and failure. Return fresh dictionaries and nested result containers on
every call, with no aliases back to input rows or later results.

render returns the run result serialized as Unicode JSON (ensure_ascii=False),
recursively sorted keys, compact separators without spaces, standard JSON
escaping, and exactly one trailing newline. Validation/domain errors propagate.

Day 2: run_many and render_many intentionally remain existing batch stubs with
their original signatures and existing batches-list check. Future extensions
must preserve the day-1 policy, input immutability, and validation-before-domain
error precedence. Batch semantics remain to be implemented.

Preserve README.md, project/compat.py, test_public.py and verify.py byte for byte;
do not delete existing files. Use only the Python standard library.
test_regression.py includes unittest.TestCase.test_domain_edge covering canonical
path collisions, highest-priority selection, first-wins ties, root and ordering.
Run `python verify.py` before claiming completion; it runs public and regression
tests and generates verification.json with command, passed_tests, failed_tests.
The report must contain at least two passes and zero failures.
