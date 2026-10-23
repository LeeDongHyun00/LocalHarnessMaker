Repaired `rotate` to normalize steps modulo length and handle empty input, while preserving type hints, values, cyclic order, and input immutability.

Added the public specification docstring and five regression tests in `test_solution.py`.

Verification passed: compilation and `python -m unittest discover -v` (5 tests).