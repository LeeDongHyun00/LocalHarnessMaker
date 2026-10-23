Refactored both functions to delegate to private `_flatten`, preserving signatures, type hints, error behavior, and input immutability.

Added four public API tests in `test_solution.py`. All pass with `python -m unittest discover -v` on Python 3.13.5.