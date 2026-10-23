Implemented `inclusive` with ascending, descending, and equal-endpoint behavior, preserving type hints.

Added six unittest methods covering ordinary ranges, boundaries, large integers, and invalid numeric inputs.

Both verification commands passed:

- `python -m py_compile solution.py test_solution.py`
- `python -m unittest discover -v` — 6 tests passed.