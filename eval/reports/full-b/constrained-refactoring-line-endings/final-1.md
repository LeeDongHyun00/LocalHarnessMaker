Both functions now delegate to `_normalize_newlines`, preserving signatures, type hints, return types, errors, input immutability, and newline behavior.

Added four public API tests in `test_solution.py`. All pass with `python -m unittest discover -v` on Python 3.13.5.