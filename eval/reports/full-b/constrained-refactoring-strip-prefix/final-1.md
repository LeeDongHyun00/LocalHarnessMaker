Both functions now delegate to one private helper in [solution.py](solution.py), preserving signatures, types, errors, input immutability, and public imports.

Added five public API tests in [test_solution.py](test_solution.py). All pass with `python -m unittest discover -v`.