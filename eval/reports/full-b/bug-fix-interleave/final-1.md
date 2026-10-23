Fixed `interleave` to append remaining items in order while preserving its signature, type hints, and input collections.

Added a regression test in `test_solution.py` covering equal lengths, unequal lengths, empty inputs, and input preservation.

Verified with `python -m unittest discover -v`: 1 test with 6 subcases passed.