Fixed `prefix` to return inclusive prefix sums while preserving input values, order, and length. Retained type hints, added the public specification docstring, and added five regression tests in `test_solution.py`.

Verification: `python -m unittest discover -v` — all five tests pass.