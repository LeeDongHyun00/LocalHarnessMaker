Both functions now delegate to private `_inclusive_range`, preserving signatures, type hints, return types, error behavior, and input immutability.

Added four public API test methods in `test_solution.py`. All pass with `python -m unittest discover -v`.