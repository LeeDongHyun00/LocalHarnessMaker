Refactored both functions to use one private `_invert` helper, preserving signatures, return types, imports, ordering, error behavior, and input immutability.

Added five public API test methods in `test_solution.py`. All pass with `python -m unittest discover -v` on Python 3.13.5.