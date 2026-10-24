Fixed `union` to merge overlapping or touching intervals in sorted order, reject reversed intervals, and preserve input. Its signature and type hints are unchanged.

Added three regression tests in `test_solution.py`. Compilation and `python -m unittest discover -v` passed.