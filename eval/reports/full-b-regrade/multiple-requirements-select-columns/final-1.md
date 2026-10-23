Repaired `select` to omit missing keys while preserving values, row and column order, and inputs. Retained type hints, added the public specification docstring, and added 8 regression tests in `test_solution.py`.

Verified with `python -m unittest discover -v`: all 8 tests pass.