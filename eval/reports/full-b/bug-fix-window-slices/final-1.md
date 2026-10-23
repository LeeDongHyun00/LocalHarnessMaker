Fixed `windows` to advance by one, return only full windows, and raise `ValueError` for nonpositive sizes. The signature and type hints are unchanged; inputs remain unmodified.

Added three regression tests in `test_solution.py`. All pass with `python -m unittest discover -v` on Python 3.13.5.