Fixed `invert` to group all keys by value in insertion order, preserving its signature and type hints without mutating input.

Added two regression tests covering grouping, order, input preservation, and empty input.

Verification passed: compilation and `python -m unittest discover -v` (2 tests).