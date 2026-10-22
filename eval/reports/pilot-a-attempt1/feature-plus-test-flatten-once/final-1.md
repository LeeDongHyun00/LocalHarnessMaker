Implemented `flatten` with preserved type hints. It flattens one level, preserves order, skips empty inner lists, and returns a new list without mutating inputs.

Added 5 unittest methods covering ordinary, boundary, empty, and non-mutation cases.

Verified: `python -m unittest discover -v` — all 5 tests passed.