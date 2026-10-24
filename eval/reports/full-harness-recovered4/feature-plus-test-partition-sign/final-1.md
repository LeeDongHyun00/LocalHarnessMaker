Implemented `partition` with type hints, preserving order and duplicates without mutating the input.

Added four unittest methods covering mixed values, boundaries, empty input, and input independence.

Verification passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v` — all 4 tests passed.