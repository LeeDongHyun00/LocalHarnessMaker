Repaired `union` to merge overlapping and touching intervals in start order, reject invalid intervals, and preserve input values and order. Added the public specification docstring and five regression tests.

Verification passed:

- `python -m py_compile solution.py`
- `python -m unittest discover -v` — all 5 tests passed.