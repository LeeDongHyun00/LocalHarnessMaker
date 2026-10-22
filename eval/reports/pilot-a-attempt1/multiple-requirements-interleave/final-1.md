Repaired `interleave` to preserve values and order, append the longer input’s remainder, and leave inputs unchanged. Retained type hints and added the public specification docstring.

Added six regression tests in `test_solution.py`. All pass with `python -m unittest discover -v`.