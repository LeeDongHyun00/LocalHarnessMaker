Build the JSON configuration inspector in inspection.py. Input values are JSON
objects/lists/scalars; object keys are strings. secret_fields is an iterable of
exact, case-sensitive key names. Use Python 3.11+ and the standard library.

SR1. inspect_config(data, secret_fields) returns one row per scalar leaf:
{'path': JSON_pointer, 'value': scalar_or_mask, 'secret': bool}. A key whose
name is in secret_fields marks its entire subtree secret, including scalars in
nested lists and objects. Once secret, descendants stay secret. Replace every
secret scalar, including null, false and numbers, with the exact string
'[redacted]'. Unmatched keys never mask merely because of a substring or case.
SR2. Paths follow RFC6901 escaping (~ -> ~0, / -> ~1), root scalar path is ''.
Array indexes are decimal. Sort final rows lexicographically by path STRING;
empty containers have no leaves. Never mutate inputs, and return independent
containers. A secret_fields generator must apply at every nesting level.
SR3. dump_config(data, secret_fields) returns inspect_config as canonical JSON:
sorted object keys, compact separators, ensure_ascii=True and no trailing LF.
No input values may appear in masked rows, including via alternate diagnostic
fields. No I/O, logging, environment lookup or global mutable configuration.
Keep the two function signatures. Add tests and run
python -m unittest discover -s . -p 'test_*.py' -v in workspace/.
