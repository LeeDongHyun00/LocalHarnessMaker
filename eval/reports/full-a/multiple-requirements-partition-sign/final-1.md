Repaired `partition` to return negatives, zeros, and positives while preserving values, relative order, and duplicates without mutating input.

Added the public specification docstring and four regression test methods in `test_solution.py`. Type hints are retained.

Verification: `python -m unittest discover -v` — all 4 tests passed.