Repaired `runs` to encode adjacent equal strings while preserving values, run order, and the input collection. Retained type hints, added the public specification docstring, and added 7 regression tests in `test_solution.py`.

Verified with `python -m unittest discover -v` on Python 3.13.5: all 7 tests pass.