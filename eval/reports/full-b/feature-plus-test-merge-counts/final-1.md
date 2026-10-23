Implemented `merge` with type hints, preserving all keys and zero/negative totals without changing either input.

Added 7 unittest tests in `test_solution.py` covering ordinary, boundary, empty, and shared-input cases.

Verified with `python -m unittest discover -v` on Python 3.13.5: all 7 tests passed.