Fixed `interleave` to append remaining items in order while preserving values, type hints, and input collections. Added the public specification docstring and 7 regression tests in `test_solution.py`.

Verified with `python -m unittest discover -v`: all 7 tests pass on Python 3.13.5.