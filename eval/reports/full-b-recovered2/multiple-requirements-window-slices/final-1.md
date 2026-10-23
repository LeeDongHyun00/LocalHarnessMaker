Fixed `windows` to return overlapping windows of exactly the requested size, reject nonpositive sizes, and preserve input values and order without mutation.

Added the public specification docstring and six regression tests in `test_solution.py`.

Verified with `python -m unittest discover -v` on Python 3.13.5: all six tests pass.