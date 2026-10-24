Refactored `words` and `words_legacy` to delegate to `_count_words`, preserving signatures, type hints, public imports, error behavior, and input immutability.

Added five public API tests in `test_solution.py`. All pass with `python -m unittest discover -v`.