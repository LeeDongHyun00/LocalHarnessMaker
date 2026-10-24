Both public functions now delegate to `_last_index`, preserving signatures, type hints, behavior, and input immutability.

Added three public API tests covering matches, absent/empty inputs, case sensitivity, immutability, and error behavior.

`python -m unittest discover -v` — all 3 tests passed.