Fixed `pairs` to return overlapping adjacent pairs, preserving its signature, type hints, and input.

Added a regression test covering ordering, short inputs, and input preservation.

Both checks passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v` (1 test)