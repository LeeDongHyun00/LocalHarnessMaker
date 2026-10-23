Fixed `union` to merge overlapping or touching intervals, reject reversed intervals, and preserve input. Signature and type hints are unchanged.

Added 3 regression tests in `test_solution.py`, including empty input.

Verified with `python -m unittest discover -v`: all 3 tests pass.