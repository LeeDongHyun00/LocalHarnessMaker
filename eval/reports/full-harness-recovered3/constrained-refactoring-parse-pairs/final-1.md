Refactored both public functions to delegate to `_parse_pairs`, preserving signatures, type hints, return types, error messages, and input immutability.

Added three public API tests covering parsing rules, invalid records, blank input, and independent results.

Compilation passed. `python -m unittest discover -v` passed all 3 tests.