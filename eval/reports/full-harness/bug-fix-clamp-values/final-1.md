Fixed `clamp` to enforce both inclusive bounds, accept equal bounds, and raise `ValueError` for reversed bounds. Preserved its signature and type hints.

Added three regression tests in `test_solution.py`. Compilation and `python -m unittest discover -v` passed.