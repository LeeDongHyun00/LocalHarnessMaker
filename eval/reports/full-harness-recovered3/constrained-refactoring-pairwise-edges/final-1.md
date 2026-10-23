Refactored both functions to delegate to `_adjacent_pairs`, preserving signatures, type hints, return types, error behavior, and input immutability.

Added five public API tests. Verification passed:

- `python -m py_compile solution.py`
- `python -m unittest discover -v` — all 5 tests passed.