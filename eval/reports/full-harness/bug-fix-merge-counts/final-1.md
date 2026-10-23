Fixed `merge` to add shared counts, retain all keys and zero/negative totals, and leave both inputs unchanged. Its signature and type hints are preserved.

Added a regression test in `test_solution.py`. Compilation and `python -m unittest discover -v` passed (1 test).