Refactored both public functions to delegate to `_common_prefix`, preserving signatures, type hints, error behavior, and input immutability.

Added four passing unittest methods covering prefixes, edge cases, immutability, and errors.

Both checks passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v`