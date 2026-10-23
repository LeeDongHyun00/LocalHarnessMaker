Fixed `pairs` to return overlapping adjacent pairs, preserving its signature, type hints, and input.

Added two regression tests in `test_solution.py` covering overlapping pairs, input preservation, and short inputs.

Verified with `python -m unittest discover -v`: both tests pass.