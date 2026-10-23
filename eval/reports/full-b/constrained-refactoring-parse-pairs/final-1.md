Refactored both functions to use one private helper, preserving signatures, type hints, return types, errors, input immutability, and import compatibility.

Added four public API tests in `test_solution.py`. All pass with `python -m unittest discover -v` on Python 3.13.5.