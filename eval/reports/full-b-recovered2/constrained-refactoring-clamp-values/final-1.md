Refactored both functions to delegate to private `_clamp`, preserving signatures, type hints, return behavior, errors, imports, and input immutability.

Added six public API tests in `test_solution.py`. All pass with `python -m unittest discover -v`.