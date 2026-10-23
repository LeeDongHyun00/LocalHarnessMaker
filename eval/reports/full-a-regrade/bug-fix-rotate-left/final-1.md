Fixed `rotate` to normalize steps modulo length and return `[]` for empty input, preserving its signature, type hints, and input collection.

Added regression tests for wrapping, negative steps, empty input, and non-mutation.

Verified: `python -m unittest discover -v` — 2 tests passed.