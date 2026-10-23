Refactored `prefix` and `prefix_legacy` to share `_prefix_sums`, preserving signatures, return types, errors, input immutability, and public imports.

Added 4 public API tests in `test_solution.py`. All pass with `python -m unittest discover -v` on Python 3.13.5.