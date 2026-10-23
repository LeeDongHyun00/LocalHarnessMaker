Fixed `select` to omit missing keys while preserving column order, row order, values, and its existing signature and type hints.

Added a regression test covering missing keys, duplicate columns, fresh dictionaries, and unchanged inputs.

Verified with `python -m unittest discover -v`: 1 test passed.