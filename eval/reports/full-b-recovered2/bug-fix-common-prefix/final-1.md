Fixed `common` to return the longest case-sensitive prefix while preserving its signature and leaving inputs unchanged.

Added regression coverage in `test_solution.py`. `python -m unittest discover -v` passes: 1 test covering 8 cases, using Python 3.13.5.