Both functions now delegate to private `_last_index`, preserving signatures, type hints, return values, error behavior, input immutability, and import compatibility.

Added five public API tests in `test_solution.py`. All pass with `python -m unittest discover -v`.