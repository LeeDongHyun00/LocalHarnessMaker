Refactored both public functions to delegate to `_balanced`, preserving signatures, type hints, error behavior, and input immutability.

Added three passing unittest methods covering nesting, unchanged input collections, and invalid inputs.

Verified compilation and `python -m unittest discover -v`.