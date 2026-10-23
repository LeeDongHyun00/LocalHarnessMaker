Repaired `invert` to group all keys in insertion order without mutating input or altering values. Preserved type hints, added the public specification docstring, and added four regression tests in `test_solution.py`.

Verification: `python -m unittest discover -v` — **all 4 tests pass**.