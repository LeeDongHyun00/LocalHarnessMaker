Refactored both functions to delegate to `_merge_counts`, preserving signatures, type hints, return types, error behavior, and input immutability.

Added four public API tests covering totals, empty inputs, shared inputs, and errors.

Verification passed: compilation, test-count check, and `python -m unittest discover -v` (4 tests).