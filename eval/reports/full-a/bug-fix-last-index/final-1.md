Fixed `last_index` to return the last matching index, preserving its signature, type hints, and input contents.

Added regression tests in `test_solution.py` for repeated matches, empty input, absent targets, and case sensitivity.

Verified: `python -m unittest discover -v` — 2 tests passed.