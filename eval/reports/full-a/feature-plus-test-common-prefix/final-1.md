Implemented `common` with case-sensitive prefix matching, preserved type hints, and no input mutation.

Added four unittest methods covering ordinary, boundary, empty, and non-mutation cases.

Verified: `python -m unittest discover -v` — all 4 tests pass.