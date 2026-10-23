Both functions now delegate to one private helper, preserving signatures, type hints, return types, error behavior, and input immutability.

Added four public API tests covering ordering, empty groups, immutability, and invalid inputs.

Verification passed: compilation and `python -m unittest discover -v` (4 tests).