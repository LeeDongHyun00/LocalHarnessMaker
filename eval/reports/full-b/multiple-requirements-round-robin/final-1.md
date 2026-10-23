Fixed `round_robin` to interleave groups in order without modifying inputs. Preserved type hints, added the public specification docstring, and added six regression tests in `test_solution.py`.

Verified with `python -m unittest discover -v`: all 6 tests pass.