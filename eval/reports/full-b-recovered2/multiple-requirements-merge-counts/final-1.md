Repaired `merge` to sum shared counts, retain zero and negative totals, preserve key order, and leave inputs unchanged. Added its public specification as a docstring and retained type hints.

Added six regression tests in `test_solution.py`. Verified with `python -m unittest discover -v`: **all 6 tests pass**.