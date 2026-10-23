Fixed `select` to omit missing keys while preserving row order, column order, values, and inputs. Added the public specification docstring and four regression tests.

Verified with `python -m unittest discover -v`: all 4 tests pass.