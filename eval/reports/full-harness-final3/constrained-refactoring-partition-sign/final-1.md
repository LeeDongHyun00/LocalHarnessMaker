Refactored both public functions to delegate to `_partition`, preserving signatures, type hints, return types, comparison order, error behavior, and input immutability.

Added four public API tests. Compilation and `python -m unittest discover -v` passed; all four tests succeeded.