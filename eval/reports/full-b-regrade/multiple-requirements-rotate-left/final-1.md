Fixed `rotate` to handle modulo wrapping, negative steps, and empty inputs while preserving values, circular order, type hints, and input collections.

Added the public specification docstring and 7 regression tests in `test_solution.py`.

Verified with `python -m unittest discover -v`: all 7 tests passed.