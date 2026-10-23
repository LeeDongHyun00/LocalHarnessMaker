Both public functions now delegate to one private helper, preserving signatures, type hints, return types, error behavior, imports, and input immutability.

Added four public API tests in `test_solution.py`.

Verified with `python -m unittest discover -v`: all 4 tests passed.