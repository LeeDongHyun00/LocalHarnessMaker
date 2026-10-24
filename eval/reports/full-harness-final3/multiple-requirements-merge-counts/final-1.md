Repaired `merge` to sum shared counts, preserve zero and negative totals, and leave both inputs unchanged. Added a public docstring defining key order and five regression tests.

Verification passed: compilation and `python -m unittest discover -v` (5 tests).