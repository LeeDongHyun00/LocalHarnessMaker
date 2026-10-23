Refactored both public functions to delegate to `_ordinal`, preserving signatures, type hints, return values, and error behavior.

Added three public API tests covering suffixes, negatives, and input immutability.

`python -m unittest discover -v` — all 3 tests passed.