Implemented `clamp` with inclusive bounds, valid equal bounds, and `ValueError` for reversed bounds. Preserved type hints.

Added 5 unittest methods in `test_solution.py` covering ordinary, boundary, and invalid inputs.

Verified: `python -m unittest discover -v` — all 5 tests pass.