Refactored both public functions to delegate to one private helper, preserving signatures, type hints, error behavior, and input immutability.

Added four public API test methods. `python -m unittest discover -v` passes all four.