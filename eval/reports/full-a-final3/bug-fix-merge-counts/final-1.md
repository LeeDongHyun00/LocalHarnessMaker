Fixed `merge` to sum shared counts, preserve zero and negative totals, and leave both inputs unchanged. Its signature and type hints remain intact.

Added a regression test in `test_solution.py`.

Verified with `python -m unittest discover -v`: 1 test passed.