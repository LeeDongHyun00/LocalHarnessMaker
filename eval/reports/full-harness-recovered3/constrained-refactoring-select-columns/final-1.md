Refactored `select` and `select_legacy` to delegate to one private helper, preserving signatures, type hints, error behavior, and input immutability.

Added four public API tests covering ordering, duplicates, missing keys, fresh dictionaries, empty inputs, and errors.

Verification passed: compilation and `python -m unittest discover -v` (4 tests).