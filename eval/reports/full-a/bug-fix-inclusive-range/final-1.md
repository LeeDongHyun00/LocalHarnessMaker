Fixed `inclusive` to include both endpoints in ascending and descending ranges, with equal endpoints returning a singleton. Preserved its signature and type hints.

Added a regression test in `test_solution.py` covering both directions, equal endpoints, and negative values.

Verified: `python -m unittest discover -v` — 1 test passed.