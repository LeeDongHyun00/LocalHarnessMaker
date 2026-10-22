Fixed `inclusive` to include both endpoints, step in either direction, and return a singleton for equal endpoints. Preserved type hints and input values, added the public docstring, and added six regression tests in `test_solution.py`.

Verified with `python -m unittest discover -v`: **all 6 tests passed**.