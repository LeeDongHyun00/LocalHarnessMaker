Implemented typed `clamp` with inclusive bounds, equal-bound support, and `ValueError` for reversed bounds.

Added four unittest methods covering ordinary, boundary, and invalid inputs.

Verification passed:
- `python -m unittest discover -v` — 4 tests passed.
- `python -m py_compile solution.py test_solution.py`