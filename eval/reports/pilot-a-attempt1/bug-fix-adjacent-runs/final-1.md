Fixed `runs` to count adjacent equal strings, keeping nonadjacent values in separate runs. Preserved its signature, type hints, and input collection.

Added regression tests for separated runs, unchanged input, and empty input.

Verification: `python -m unittest discover -v` — 2 tests passed.