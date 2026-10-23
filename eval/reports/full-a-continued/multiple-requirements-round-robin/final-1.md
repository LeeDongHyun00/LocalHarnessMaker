Repaired `round_robin` to interleave groups in order while preserving values and leaving inputs unchanged. Added the public specification docstring, retained type hints, and added five regression tests in `test_solution.py`.

Verified with `python -m unittest discover -v`: all five tests pass.