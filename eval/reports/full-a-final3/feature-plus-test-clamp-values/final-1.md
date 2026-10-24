Implemented `clamp` with inclusive bounds, valid equal bounds, and `ValueError` for reversed bounds. Preserved type hints.

Added four unittest methods in `test_solution.py` covering ordinary values, boundaries, equal bounds, and invalid bounds.

Verified: `python -m unittest discover -v` — all 4 tests pass.