Refactored both functions to delegate to private `_select`, preserving signatures, type hints, imports, return behavior, errors, and input immutability.

Added four public API tests in `test_solution.py`. All pass with `python -m unittest discover -v`.