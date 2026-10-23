Refactored `partition` and `partition_legacy` to share one private helper, preserving signatures, type hints, return types, ordering, duplicates, error behavior, and input immutability.

Added six public API tests in `test_solution.py`. All pass with `python -m unittest discover -v`.