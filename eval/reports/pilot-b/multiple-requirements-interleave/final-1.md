Fixed `interleave` to append remainders in order, handle empty inputs, and preserve values without mutating inputs. Retained type hints, added the public specification docstring, and added six regression test methods in `test_solution.py`.

Verified with `python -m unittest discover -v`: all 6 tests pass.