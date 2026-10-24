Fix resolve(defaults, file_values, environment, prefix='APP_') in settings.py.
It returns a fresh dict whose values are Setting(value, source). A source is one
of 'default', 'file', 'environment'. Inputs are mappings; environment values are strings.
The current implementation loses explicit empty overrides and their provenance.

OR1. Resolve the union of keys from defaults and file_values and prefixed environment
names. An environment name contributes its suffix lowercased; ignore nonprefixed
names and an empty suffix. Defaults/file keys are already lower-case. Precedence
is environment > file > default by key presence, including '', 0, False, None, [], {}.
OR2. Parse only environment values: the exact strings 'true', 'false', 'null' become
True, False, None; an optional minus sign followed by one or more ASCII digits
becomes int (leading zeros allowed); all other text, including whitespace, '+2',
Unicode digits and empty strings, stays a string. Never parse default/file values.
OR3. Setting.source must name the winning layer even for an empty value. Deep-copy
chosen values so mutating a returned nested list/dict cannot change either input.
Do not mutate inputs during resolution. Distinct calls/results must be independent.
Environment suffix collisions after lowercasing use the last mapping entry.

Use Python 3.11+ and the standard library. Preserve the documented public API.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
Change application code and add regression tests as needed.
