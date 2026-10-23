Fixed `parse_pairs` while preserving its signature and type hints. It now handles whitespace, blank lines, repeated keys, embedded equals signs, empty values, and invalid records as specified.

Added four regression tests in `test_solution.py`.

Verified with `python -m unittest discover -v`: **all 4 tests passed**.