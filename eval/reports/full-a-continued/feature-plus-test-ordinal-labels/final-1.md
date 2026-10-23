Implemented `ordinal` with correct suffixes, teen exceptions, `0th`, and `ValueError` for negatives. Preserved type hints.

Added 3 unittest methods covering ordinary values, boundaries, large integers, and negatives.

Verification: `python -m unittest discover -v` — all 3 tests passed.