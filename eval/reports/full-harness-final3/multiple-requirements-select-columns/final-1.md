Fixed `select` to omit missing keys while preserving column order, row order, values, and input collections. Retained type hints and added the public specification docstring.

Added four regression tests in `test_solution.py`. Compilation and `python -m unittest discover -v` both pass.