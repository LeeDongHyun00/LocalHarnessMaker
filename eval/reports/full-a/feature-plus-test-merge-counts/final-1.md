Implemented `merge` with type hints, preserving all keys, zero and negative totals, and leaving both inputs unchanged.

Added 4 unittest methods covering ordinary, boundary, empty, and shared-input cases.

Verified with `python -m unittest discover -v`: all 4 tests pass.