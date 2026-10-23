Implemented `flatten` to flatten exactly one level, preserve order, ignore empty lists, and return a new list without mutating inputs. Type hints are preserved.

Added 7 tests in `test_solution.py` covering ordinary, boundary, empty, and nested inputs.

Verified with `python -m unittest discover -v` on Python 3.13.5: all 7 tests pass.