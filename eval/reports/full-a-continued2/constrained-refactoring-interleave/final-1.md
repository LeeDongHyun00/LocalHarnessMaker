Refactored both public functions to delegate to `_interleave`, preserving signatures, type hints, return types, error behavior, and input immutability.

Added four public API tests covering alternation, remainders, empty inputs, immutability, and invalid inputs.

Verification: `python -m unittest discover -v` — all 4 tests passed.