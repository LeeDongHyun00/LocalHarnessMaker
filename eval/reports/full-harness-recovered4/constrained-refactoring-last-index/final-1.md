Refactored both public functions to delegate to one private helper, preserving signatures, type hints, error behavior, and input immutability.

Added three public API tests covering matching, empty and absent inputs, case sensitivity, immutability, and invalid inputs.

`python -m unittest discover -v` passed all 3 tests.