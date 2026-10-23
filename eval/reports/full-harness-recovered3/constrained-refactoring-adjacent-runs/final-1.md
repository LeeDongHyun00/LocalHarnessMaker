Refactored both functions to delegate to `_encode_runs`, preserving signatures, type hints, error behavior, and input immutability.

Added four public API tests covering run grouping, empty input, immutability, and invalid input.

Both checks passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v` — 4 tests passed.