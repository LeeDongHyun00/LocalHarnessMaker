Both functions now delegate to private `_balanced`, preserving signatures, type hints, return types, error behavior, input immutability, and public imports.

Added five public API test methods. All pass with `python -m unittest discover -v`.