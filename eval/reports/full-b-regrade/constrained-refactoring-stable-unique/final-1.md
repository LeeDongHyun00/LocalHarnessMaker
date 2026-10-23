Refactored `unique` and `unique_legacy` to share private helper `_unique`, preserving signatures, type hints, return types, errors, imports, and input immutability.

Added five public API tests. All pass with `python -m unittest discover -v`.