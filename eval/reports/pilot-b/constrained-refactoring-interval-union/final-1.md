Refactored `union` and `union_legacy` to delegate to `_merge_intervals`, preserving signatures, type hints, return types, error behavior, imports, and input immutability.

Added five public API tests in `test_solution.py`. All pass with `python -m unittest discover -v` on Python 3.13.5.