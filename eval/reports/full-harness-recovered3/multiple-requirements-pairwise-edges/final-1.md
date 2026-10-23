Fixed `pairs` to return overlapping adjacent pairs in input order without mutating inputs. Preserved type hints, added the public specification docstring, and added four regression tests.

Verification passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v` — all 4 tests passed.