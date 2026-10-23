Repaired `clamp`, added its public specification docstring, and preserved type hints.

Added 5 passing regression tests covering inclusive bounds, out-of-range values, equal bounds, invalid ranges, and input collection preservation and order.

Both compilation and `python -m unittest discover -v` passed.