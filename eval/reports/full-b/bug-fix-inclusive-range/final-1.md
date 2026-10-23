Fixed `inclusive` to include both endpoints in ascending or descending order and return a singleton for equal endpoints. Preserved its signature and type hints.

Added a regression test in `test_solution.py` covering all three cases.

Verified with `python -m unittest discover -v`: 1 test passed.