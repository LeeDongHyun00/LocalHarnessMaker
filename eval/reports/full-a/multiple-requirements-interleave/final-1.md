Fixed `interleave` to append the longer input’s remainder while preserving values, order, type hints, and input collections. Added the public specification docstring and six regression tests in `test_solution.py`.

Verified with `python -m unittest discover -v`: all 6 tests pass.