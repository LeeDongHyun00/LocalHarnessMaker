Implemented `last_index` with preserved type hints and no input mutation.

Added five unittest methods covering repeated matches, absent targets, boundary positions, empty inputs, case sensitivity, and input preservation.

Verification passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v` — all 5 tests passed.