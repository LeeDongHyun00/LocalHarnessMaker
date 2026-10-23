Repaired `union` to merge overlapping or touching intervals, sort by start, and reject reversed intervals without mutating input values or order.

Added the public specification docstring and five regression tests in `test_solution.py`.

Verified with `python -m unittest discover -v`: all 5 tests pass.