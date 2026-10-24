Fixed `pairs` to return overlapping adjacent pairs in order, preserving its signature, type hints, and input.

Added regression tests for overlapping pairs, input preservation, and short inputs.

Verified with `python -m unittest discover -v`: 2 tests passed.