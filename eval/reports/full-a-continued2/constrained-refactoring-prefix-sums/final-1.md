Refactored `prefix` and `prefix_legacy` to delegate to one private helper, preserving signatures, type hints, return types, error behavior, and input immutability.

Added 3 public API test methods in `test_solution.py`.

Verification: `python -m unittest discover -v` — all 3 tests passed.