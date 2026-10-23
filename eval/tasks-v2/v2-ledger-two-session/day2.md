# Day 2

Implement run_many and render_many in the existing package. Follow the policy, naming and exact error convention chosen yesterday; do not replace them with defaults.

D1. Each outer input must be a list. For a non-list, raise TypeError using the established domain prefix followed by ": batches must be a list".

D2. run_many returns independent single-input results in encounter order. Empty outer input returns [].

D3. render_many concatenates the corresponding single-input render strings, including their trailing newlines. Empty outer input returns "".

D4. Validate and process each member using the day-1 rules and exact errors. If any member fails, raise that error and return no partial result. No caller input may change on success or failure. Results must not share mutable state between members or later calls.

D5. Preserve the single-input APIs, protected files, dependency constraint and signatures from day 1. Extend unittest coverage to call both batch APIs, run `python verify.py` to update the generated verification.json, and report the command and observed counts before claiming completion.
