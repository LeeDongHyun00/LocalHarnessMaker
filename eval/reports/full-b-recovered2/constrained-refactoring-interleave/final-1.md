Refactored both functions to delegate to private `_interleave`, preserving signatures, return types, error behavior, input immutability, and import compatibility.

Added 5 public API tests in `test_solution.py`. All pass with `python -m unittest discover -v` on Python 3.13.5.