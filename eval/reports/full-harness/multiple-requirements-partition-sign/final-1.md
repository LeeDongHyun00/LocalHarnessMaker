Repaired `partition` to return negatives, zeros, and positives while preserving values, order, and duplicates without mutating input. Retained type hints and added the public specification docstring.

Added four regression tests in `test_solution.py`. Compilation and `python -m unittest discover -v` passed.