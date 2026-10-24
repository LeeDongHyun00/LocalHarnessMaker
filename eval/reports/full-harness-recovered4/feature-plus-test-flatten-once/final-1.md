Implemented `flatten` with type hints, preserving order and flattening exactly one level without mutating inputs.

Added five unittest tests covering ordinary, boundary, empty, and nested inputs, plus input preservation.

Verified: `python -m unittest discover -v` — all five tests pass.