Fixed `unique` to preserve first-occurrence order, case-sensitive equality, exact string values, and unchanged input. Added its public specification docstring and six regression tests in `test_solution.py`.

Verified with `python -m unittest discover -v` on Python 3.13.5: all 6 tests pass.