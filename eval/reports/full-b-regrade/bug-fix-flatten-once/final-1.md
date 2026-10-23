Fixed `flatten` to flatten exactly one level, preserve order, skip empty lists, and return a new list without mutating inputs. Signature and type hints are unchanged.

Added a regression test in `test_solution.py`.

Verified with `python -m unittest discover -v`: 1 test passed.