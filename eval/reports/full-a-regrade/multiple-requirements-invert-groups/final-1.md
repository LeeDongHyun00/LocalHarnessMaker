Fixed `invert` to retain all keys grouped by value in insertion order without mutating the input. Added the public specification docstring and four regression tests.

Verified with `python -m unittest discover -v`: all 4 tests pass.