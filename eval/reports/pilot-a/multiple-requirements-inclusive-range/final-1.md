Fixed `inclusive` to include both endpoints in ascending or descending order, with equal endpoints returning a singleton. Preserved type hints and added the public specification docstring.

Added five regression tests in `test_solution.py`, including input preservation and collection order.

Verification: `python -m unittest discover -v` — all 5 tests passed.