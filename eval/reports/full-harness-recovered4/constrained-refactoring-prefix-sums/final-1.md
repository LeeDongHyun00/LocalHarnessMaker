Refactored both functions to delegate to `_prefix_sums`, preserving signatures, type hints, error behavior, and input immutability.

Added two passing unittest methods covering inclusive sums, empty input, negative values, immutability, and invalid inputs.

Verification passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v`