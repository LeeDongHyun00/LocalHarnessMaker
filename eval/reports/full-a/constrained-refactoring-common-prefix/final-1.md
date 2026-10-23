Refactored both functions to delegate to `_common_prefix`, preserving signatures, type hints, error behavior, and input immutability.

Added 3 public API tests covering prefix behavior, immutability, and errors.

`python -m unittest discover -v` — all 3 tests passed.