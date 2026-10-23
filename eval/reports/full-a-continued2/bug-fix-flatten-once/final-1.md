Fixed `flatten` to flatten exactly one list level, preserving order and skipping empty lists without mutating inputs. Its signature and type hints are unchanged.

Added two regression tests in `test_solution.py`. Both pass with `python -m unittest discover -v`.