Fixed `partition` to return negatives, zeros, and positives while preserving order and duplicates. Input remains unchanged; signature and type hints are preserved.

Added a regression test in `test_solution.py`, confirmed it failed before the fix, and verified `python -m unittest discover -v` now passes: 1 test.