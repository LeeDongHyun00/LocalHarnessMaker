Fixed `last_index` to return the last matching index, preserving its signature, type hints, and input.

Added two regression tests covering duplicates, absent targets, empty input, case sensitivity, and input preservation.

Verification passed: compilation and `python -m unittest discover -v` (2 tests).