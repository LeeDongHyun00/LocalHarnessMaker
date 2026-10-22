Refactored `union` and `union_legacy` to delegate to private `_union`, preserving signatures, type hints, return types, error behavior, and input immutability.

Added three public API tests. All pass with `python -m unittest discover -v` on Python 3.13.5.