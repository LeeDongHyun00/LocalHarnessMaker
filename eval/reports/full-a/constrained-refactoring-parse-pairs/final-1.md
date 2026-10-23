Refactored both public functions to delegate to `_parse_pairs`, preserving signatures, type hints, return types, error behavior, and input immutability.

Added four public API tests in `test_solution.py`. All pass with `python -m unittest discover -v`.