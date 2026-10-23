Fixed `windows` to return overlapping, exact-size windows and raise `ValueError` for nonpositive sizes. Preserved its signature, type hints, and input.

Added three regression tests in `test_solution.py`. All pass with `python -m unittest discover -v`.