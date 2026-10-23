Fixed `clamp` to enforce both inclusive bounds, accept equal bounds, and raise `ValueError` when `low > high`. Preserved its signature and type hints.

Added 3 regression tests in `test_solution.py`. Verified with `python -m unittest discover -v`: all 3 pass.