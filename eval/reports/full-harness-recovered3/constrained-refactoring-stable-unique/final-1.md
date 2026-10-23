Refactored both functions to delegate to `_unique`, preserving signatures, type hints, error behavior, ordering, case sensitivity, and input immutability.

Added three public API tests. `python -m unittest discover -v` passes all three.