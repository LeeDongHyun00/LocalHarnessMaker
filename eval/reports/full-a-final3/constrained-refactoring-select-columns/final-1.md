Refactored `select` and `select_legacy` to delegate to one private helper, preserving signatures, type hints, error behavior, and input immutability.

Added four public API tests in `test_solution.py`. All pass with `python -m unittest discover -v`.