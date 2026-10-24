Refactored both functions to delegate to one private helper, preserving signatures, type hints, return types, and error behavior.

Added four public tests covering ascending and descending ranges, equal endpoints, invalid inputs, and input immutability.

Compilation passed; `python -m unittest discover -v` passed all four tests.