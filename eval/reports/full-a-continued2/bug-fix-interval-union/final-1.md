Fixed `union` to merge overlapping or touching intervals, sort by start, and reject reversed intervals without mutating input. Preserved its signature and type hints.

Added three regression tests in `test_solution.py`. All pass with `python -m unittest discover -v`.