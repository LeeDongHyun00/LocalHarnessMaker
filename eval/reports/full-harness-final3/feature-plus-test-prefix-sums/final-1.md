Implemented `prefix` with inclusive sums, preserved type hints, and no input mutation.

Added three unittest methods covering ordinary, negative, boundary, and empty inputs.

Verification passed:
- `python -m py_compile solution.py test_solution.py`
- `python -m unittest discover -v` — all 3 tests passed.