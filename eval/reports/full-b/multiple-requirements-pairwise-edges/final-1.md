Fixed `pairs` to return overlapping adjacent pairs without mutating inputs or changing values or order. Added the public specification docstring, retained type hints, and added five regression tests in `test_solution.py`.

Verified with `python -m unittest discover -v` on Python 3.13.5: all five tests passed.