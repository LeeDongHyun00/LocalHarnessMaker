Fixed `clamp` to enforce both inclusive bounds, allow equal bounds, and raise `ValueError` for reversed bounds. Preserved type hints and added the public specification docstring.

Added six regression tests covering boundaries, errors, unchanged inputs, and collection order.

Verification: `python -m unittest discover -v` — all 6 tests passed.