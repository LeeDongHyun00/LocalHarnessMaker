Fixed `rotate` to normalize steps modulo length and handle empty input, preserving values, cyclic order, type hints, and input collections.

Added the public specification docstring and six regression tests in `test_solution.py`.

Verified: `python -m unittest discover -v` — all 6 tests pass.