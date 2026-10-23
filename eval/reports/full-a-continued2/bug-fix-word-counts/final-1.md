Fixed `words` to split on arbitrary whitespace, casefold tokens, and count them while preserving punctuation and its signature.

Added two regression tests in `test_solution.py`, including empty input coverage.

Verified: `python -m unittest discover -v` — both tests passed.