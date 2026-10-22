Refactored `invert` and `invert_legacy` to share one private helper, preserving signatures, type hints, return types, ordering, errors, imports, and input immutability.

Added five public API tests in `test_solution.py`. All pass with `python -m unittest discover -v`.