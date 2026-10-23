Refactored both functions to delegate to one private helper, preserving signatures, type hints, newline behavior, errors, and input immutability.

Added three public API tests in `test_solution.py`. All pass with `python -m unittest discover -v`.