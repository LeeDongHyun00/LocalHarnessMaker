Repaired `unique` to preserve first-occurrence order, case-sensitive equality, and input values without mutating the input. Retained type hints and added the public specification docstring.

Added five regression tests in `test_solution.py`. All pass with `python -m unittest discover -v`.