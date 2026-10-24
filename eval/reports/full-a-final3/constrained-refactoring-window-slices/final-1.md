Refactored both functions to delegate to private `_windows`, preserving signatures, type hints, return types, error messages, and input immutability.

Added four public API tests in `test_solution.py`. All pass with `python -m unittest discover -v`.