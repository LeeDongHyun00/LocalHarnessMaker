Fixed `partition` to return negatives, zeros, and positives while preserving values, relative order, and duplicates without mutating input. Added its public specification docstring and retained type hints.

Added 5 regression tests in `test_solution.py`. All pass with `python -m unittest discover -v`.