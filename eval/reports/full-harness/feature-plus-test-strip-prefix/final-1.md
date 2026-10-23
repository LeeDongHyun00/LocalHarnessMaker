Implemented `strip_prefix` with preserved type hints, removing exactly one matching prefix.

Added 5 unittest methods covering ordinary, boundary, empty, nonmatching, and repeated-prefix cases.

Verification passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v` — all 5 tests passed.