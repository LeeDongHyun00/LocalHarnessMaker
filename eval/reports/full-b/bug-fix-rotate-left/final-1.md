Fixed `rotate` to normalize steps modulo length and return `[]` for empty input, preserving its signature, type hints, and input collections.

Added regression tests in `test_solution.py` covering positive and negative steps, wraparound, empty input, and non-mutation.

Verified: `python -m unittest discover -v` — 2 tests passed.