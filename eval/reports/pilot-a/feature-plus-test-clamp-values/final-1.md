Implemented `clamp` with inclusive bounds and `ValueError` for reversed bounds, preserving type hints.

Added four unittest methods covering ordinary values, boundaries, equal bounds, and invalid bounds.

Verified: `python -m unittest discover -v` — all 4 tests pass.