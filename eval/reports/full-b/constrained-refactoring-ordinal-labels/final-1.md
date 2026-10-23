Refactored both functions to delegate to `_format_ordinal`, preserving signatures, type hints, return types, errors, input immutability, and import compatibility.

Added 4 public API tests. All pass with `python -m unittest discover -v`.