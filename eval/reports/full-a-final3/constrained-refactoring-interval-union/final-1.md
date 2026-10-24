Refactored `union` and `union_legacy` to delegate to one private `_union` helper, preserving signatures, type hints, return types, errors, and input immutability.

Added 3 public API tests in `test_solution.py`. All pass with `python -m unittest discover -v`.