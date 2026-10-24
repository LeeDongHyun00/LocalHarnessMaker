Refactored both functions to delegate to `_windows`, preserving signatures, type hints, return types, error messages, and input immutability.

Added four public API tests covering windows, boundaries, errors, and immutability.

Both checks passed:

- `python -m py_compile solution.py`
- `python -m unittest discover -v` — 4 tests passed.