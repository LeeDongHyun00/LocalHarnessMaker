Fixed `partition` to return negatives, zeros, and positives in order, preserving relative order and duplicates without mutating input. The signature and type hints are unchanged.

Added two regression tests in `test_solution.py`. Both pass with `python -m unittest discover -v`.