Refactored both public functions to delegate to `_interleave`, preserving signatures, type hints, return types, error behavior, and input immutability.

Added three public API tests covering alternation, remainders, empty inputs, immutability, and invalid inputs.

Compilation and `python -m unittest discover -v` passed.