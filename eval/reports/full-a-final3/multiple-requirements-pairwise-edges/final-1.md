Fixed `pairs` to return overlapping adjacent pairs while preserving input values and order without mutation. Retained type hints, added the public specification docstring, and added 3 regression test methods.

Verified with `python -m unittest discover -v`: all 3 tests pass.