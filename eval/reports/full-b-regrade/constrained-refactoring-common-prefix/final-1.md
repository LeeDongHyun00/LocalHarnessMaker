Both functions now delegate to `_common_prefix`, preserving signatures, type hints, imports, return behavior, errors, and input immutability.

Added 5 public API tests in `test_solution.py`. All pass with `python -m unittest discover -v`.