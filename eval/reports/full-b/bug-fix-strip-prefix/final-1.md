Fixed `strip_prefix` using `str.removeprefix`, preserving its signature and type hints. Added regression coverage for repeated, nonmatching, and empty prefixes.

Verified with `python -m unittest discover -v`: 1 test passed.