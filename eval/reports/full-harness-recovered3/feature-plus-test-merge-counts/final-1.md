Implemented `merge` with existing type hints, preserving zero and negative totals without mutating either input.

Added four unittest methods covering ordinary, boundary, empty, and shared-input cases.

Verification passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v` — all 4 tests passed.