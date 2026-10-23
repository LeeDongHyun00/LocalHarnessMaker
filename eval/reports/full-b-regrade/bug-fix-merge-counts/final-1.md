Fixed `merge` without changing its signature or type hints. It now adds shared counts, preserves zero and negative totals, and leaves both inputs unchanged.

Added two regression tests in `test_solution.py`.

Verified with `python -m unittest discover -v`: **2 tests passed**.