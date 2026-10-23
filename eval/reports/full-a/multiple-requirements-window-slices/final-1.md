Fixed `windows` to return exact-size windows advancing by one, reject nonpositive sizes, and preserve input values and order.

Added the public specification docstring and six regression tests in `test_solution.py`.

Verified: `python -m unittest discover -v` — all 6 tests pass.