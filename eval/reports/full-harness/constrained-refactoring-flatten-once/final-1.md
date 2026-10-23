Refactored both public functions to delegate to `_flatten`, preserving signatures, type hints, behavior, and input immutability.

Added four public API tests covering order, empty lists, one-level flattening, fresh results, immutability, and TypeErrors.

Verified: `python -m unittest discover -v` — all four tests pass.