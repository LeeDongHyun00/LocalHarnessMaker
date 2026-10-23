Both functions now delegate to private `_count_words`, preserving signatures, type hints, return types, error behavior, and input immutability.

Added six public API tests. All pass with `python -m unittest discover -v`.