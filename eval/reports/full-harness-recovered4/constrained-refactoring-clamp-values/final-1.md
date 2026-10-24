Refactored both functions to use private `_clamp`, preserving signatures, type hints, return behavior, and errors.

Added four passing public API tests covering inclusive clamping, equal bounds, reversed bounds, and input immutability.

Verification passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v`