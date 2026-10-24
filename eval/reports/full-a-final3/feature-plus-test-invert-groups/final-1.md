Implemented `invert` with type hints, preserving key insertion order without mutating input.

Added four unittest tests covering grouping, input preservation, single-item and empty-string boundaries, and empty input.

Verified: `python -m unittest discover -v` — all 4 tests pass.