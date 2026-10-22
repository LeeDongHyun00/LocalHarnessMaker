Fixed `runs` to count adjacent equal strings separately, preserving its signature, type hints, and input.

Added regression tests in `test_solution.py` for separate runs, empty input, and input preservation.

Verified with `python -m unittest discover -v`: 2 tests pass.