Both public functions now delegate to one private helper, preserving signatures, type hints, return values, and error behavior.

Added four public API tests covering single-prefix removal, unchanged inputs, input immutability, and runtime errors.

Verification passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v` — all 4 tests passed.