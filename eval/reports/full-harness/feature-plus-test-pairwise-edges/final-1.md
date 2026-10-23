Implemented `pairs` with preserved type hints and no input mutation. Added five unittest tests covering ordinary, boundary, empty inputs, and input preservation.

Verification passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v` — all 5 tests passed.