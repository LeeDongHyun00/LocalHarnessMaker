Fixed `clamp` to enforce both inclusive bounds and raise `ValueError` when `low > high`, preserving its signature and type hints.

Added three regression tests covering range boundaries, equal bounds, and reversed bounds.

Verification: `python -m unittest discover -v` — all 3 tests passed.