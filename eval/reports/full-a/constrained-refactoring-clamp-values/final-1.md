Refactored `clamp` and `clamp_legacy` to delegate to one private `_clamp` helper, preserving signatures, type hints, return behavior, error messages, and input immutability.

Added four public API tests in `test_solution.py`. All pass with `python -m unittest discover -v` on Python 3.13.5.