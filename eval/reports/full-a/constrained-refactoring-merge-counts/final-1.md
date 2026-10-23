Refactored `merge` and `merge_legacy` to delegate to one private helper, preserving signatures, type hints, return types, error behavior, and input immutability.

Added four public API tests in `test_solution.py`. All pass with `python -m unittest discover -v` on Python 3.13.5.