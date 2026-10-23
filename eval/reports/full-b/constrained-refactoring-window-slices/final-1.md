Both functions now delegate to one private helper, preserving signatures, type hints, return types, error behavior, imports, public names, and input immutability.

Added four public API tests in `test_solution.py`. All pass with `python -m unittest discover -v`.