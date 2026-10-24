Implemented `select` with ordered, deduplicated columns, omitted missing keys, preserved values and row order, and new dictionaries without mutating inputs.

Added 4 unittest methods covering ordinary, boundary, empty, and non-mutation cases.

Verified: `python -m unittest discover -v` — all 4 tests pass.