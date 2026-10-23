Refactored `flatten` and `flatten_legacy` to share private `_flatten`, preserving signatures, type hints, behavior, errors, and input immutability.

Added 5 public API tests. All pass with `python -m unittest discover -v` on Python 3.13.5.