Fixed `select` to omit missing keys while preserving order, values, unique column names, and inputs. Signature and type hints are unchanged.

Added a regression test in `test_solution.py`. Verified with `python -m unittest discover -v`: 1 test passed.