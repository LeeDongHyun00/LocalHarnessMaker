Fixed `select` to omit missing keys while preserving column order, values, row order, and its existing signature.

Added a regression test covering duplicate columns, missing keys, fresh dictionaries, and unchanged inputs.

Validation passed: compilation and `python -m unittest discover -v` (1 test).