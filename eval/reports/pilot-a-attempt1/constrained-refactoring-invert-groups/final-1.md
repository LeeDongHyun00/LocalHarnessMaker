Refactored `invert` and `invert_legacy` to delegate to private `_invert`, preserving signatures, type hints, ordering, error behavior, and input immutability.

Added four public API tests in `test_solution.py`. All pass with `python -m unittest discover -v`.