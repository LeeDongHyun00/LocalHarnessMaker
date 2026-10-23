Fixed `unique` to preserve first-occurrence order, case-sensitive equality, and input values without mutating the input. Retained type hints, added the public specification docstring, and added four regression tests in `test_solution.py`.

Verification passed: compilation and `python -m unittest discover -v` (4 tests).