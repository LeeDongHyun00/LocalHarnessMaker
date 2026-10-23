Refactored both functions to delegate to private `_pairs`, preserving signatures, type hints, return types, error behavior, and input immutability.

Added four public API tests in `test_solution.py`. All pass with `python -m unittest discover -v`.