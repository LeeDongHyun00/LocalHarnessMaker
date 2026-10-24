Repaired `windows` to return every contiguous window of exactly `size`, advancing by one. It now raises `ValueError` for nonpositive sizes and preserves input values and order.

Added the specification docstring and five regression tests in `test_solution.py`.

Verification passed: compilation and `python -m unittest discover -v` (5 tests).