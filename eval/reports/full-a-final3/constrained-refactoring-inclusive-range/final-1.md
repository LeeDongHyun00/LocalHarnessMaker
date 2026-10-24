Refactored both functions to delegate to private `_inclusive`, preserving signatures, type hints, list returns, error behavior, and input immutability.

Added 3 public API tests covering ranges, invalid inputs, and collection immutability. All pass with `python -m unittest discover -v`.