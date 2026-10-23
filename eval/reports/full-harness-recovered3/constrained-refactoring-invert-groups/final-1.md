Refactored both functions to delegate to private `_invert`, preserving signatures, type hints, ordering, error behavior, and input immutability.

Added four public API tests. All pass with `python -m unittest discover -v`; compilation also passes.