Fixed `partition` to return negatives, zeros, and positives in order, preserving duplicates and relative order without mutating input. Signature and type hints remain unchanged.

Added two regression tests covering mixed values and empty input.

Verification passed: compilation and `python -m unittest discover -v` (2 tests).