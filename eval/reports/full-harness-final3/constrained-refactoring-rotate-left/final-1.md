Refactored both functions to delegate to `_rotate`, preserving signatures, type hints, return behavior, errors, and input immutability.

Added three public API unittest methods covering rotation, edge cases, and invalid steps.

Both compilation and `python -m unittest discover -v` passed.