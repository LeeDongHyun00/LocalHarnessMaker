Fixed `invert` to group all keys sharing a value in insertion order, preserving its signature and type hints without mutating the input.

Added two regression tests in `test_solution.py`. Both pass with `python -m unittest discover -v`.