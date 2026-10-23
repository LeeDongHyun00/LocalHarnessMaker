Fixed `last_index` to return the last matching index while preserving its signature, type hints, and input.

Added regression coverage for duplicates, absent targets, empty input, and case sensitivity.

Verified: `python -m unittest discover -v` — 1 test passed with 6 subcases.