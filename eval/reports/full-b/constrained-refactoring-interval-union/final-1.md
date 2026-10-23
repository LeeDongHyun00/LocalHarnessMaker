Refactored both functions to delegate to `_merge_intervals`, preserving signatures, type hints, return types, error behavior, and input immutability.

Added 5 public API tests in `test_solution.py`. All pass with `python -m unittest discover -v` on Python 3.13.5.