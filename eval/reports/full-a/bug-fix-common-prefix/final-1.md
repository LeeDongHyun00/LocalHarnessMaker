Fixed `common` to return the longest case-sensitive character prefix, preserving its signature, type hints, and input collections.

Added regression coverage in `test_solution.py` for shared prefixes, empty input, single items, case sensitivity, and input preservation.

`python -m unittest discover -v` passed.