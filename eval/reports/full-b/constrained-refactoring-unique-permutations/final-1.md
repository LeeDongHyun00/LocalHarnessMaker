Both functions now delegate to one private helper in [solution.py](solution.py), preserving signatures, return types, errors, imports, and input immutability.

Added six public API tests in [test_solution.py](test_solution.py). All passed with `python -m unittest discover -v` on Python 3.13.5.