Ship the policy v1-to-v2 migration, compatible reader and operator instructions.
Keep migrate(data)->dict, Policy(data).allows(subject,action)->bool and export()->dict,
and add `python policy.py SOURCE DESTINATION`.
Input is valid policy data: v1 has version:1 and users mapping subjects to action
lists; v2 has version:2, default:'deny', and rules with exact subject/action and
effect 'allow' or 'deny'. Names are literal strings: '*' is not a wildcard.

PM1. migrate(v1) emits version 2, default deny and one allow rule for each unique (subject,action). Sort by subject then action using Python string order. Do not mutate input. migrate(v2) is a deep-copy identity; unsupported versions raise ValueError('version').
PM2. Policy reads both versions. Grant only an explicit matching allow; a matching deny wins regardless of order. Unknown subject/action pairs and empty policies deny. No wildcard or inherited privilege exists.
PM3. export returns an independent v2 copy; mutating either source or exported nested structures must not affect the live reader. Migrated v1 permissions must agree with the compatible v1 reader after export/reload.
PM4. CLI reads UTF-8 JSON, writes canonical JSON (sort_keys=True, indent=2, final newline) to a new destination only, and leaves source bytes untouched. Success: exit 0, stdout 'migrated' plus newline, empty stderr. Malformed input, unsupported version, missing source or existing destination: exit 2, empty stdout, stderr 'migration failed' plus newline; never replace an existing destination or create output for invalid input.
PM5. Create MIGRATION.md naming the runnable command `python policy.py SOURCE DESTINATION` and containing sections `## Compatibility`, `## Default deny`, `## Rollback`. Explain v1/v2 support, unknown pairs denied and explicit-deny precedence, and instruct operators to retain the original source for rollback. Include a valid fenced `json` v1 example: its users must have at least two subjects and one repeated action. The example must migrate with unchanged effective permissions.

Use Python 3.11+ and only the standard library. Preserve the stated APIs.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
