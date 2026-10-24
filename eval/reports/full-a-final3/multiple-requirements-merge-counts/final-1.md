Repaired `merge` to add shared counts, retain zero and negative totals, preserve key order, and leave both inputs unchanged. Type hints remain intact.

Added the public specification docstring and five regression tests in `test_solution.py`.

Verified: `python -m unittest discover -v` — all 5 tests pass.