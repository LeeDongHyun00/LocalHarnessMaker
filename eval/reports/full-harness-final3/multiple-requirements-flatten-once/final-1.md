Repaired `flatten` to preserve every value and its order while flattening exactly one level, skipping empty inner lists, and leaving inputs unchanged.

Added the public specification docstring and four regression tests in `test_solution.py`.

Verification passed: compilation and `python -m unittest discover -v` (4 tests).