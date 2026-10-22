Fixed `runs` to count adjacent equal strings separately, preserving its signature, type hints, and input.

Added regression tests for nonadjacent repeats, input preservation, and empty input.

Verified with `python -m unittest discover -v`: 2 tests passed.