Fixed `strip_prefix` using `str.removeprefix`, preserving its signature and type hints.

Added a regression test covering matching, repeated, nonmatching, and empty prefixes.

Verification passed: Python compilation and `python -m unittest discover -v` (1 test).