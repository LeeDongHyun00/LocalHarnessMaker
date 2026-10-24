Refactored both functions to delegate to private `_invert`, preserving signatures, type hints, ordering, errors, and input immutability.

Added five public API tests in `test_solution.py`. All pass with `python -m unittest discover -v` on Python 3.13.5.