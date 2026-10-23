Implemented `strip_prefix` using `str.removeprefix`, preserving type hints and removing exactly one matching prefix.

Added four unittest methods covering ordinary, repeated, nonmatching, boundary, and empty inputs.

Verified with `python -m unittest discover -v`: all 4 tests pass.