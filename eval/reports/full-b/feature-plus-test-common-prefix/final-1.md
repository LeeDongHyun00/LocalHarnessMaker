Implemented `common` with case-sensitive prefix matching, preserved type hints, and no input mutation.

Added 8 unittest methods covering ordinary, boundary, empty, single-item, Unicode, and case-sensitive inputs.

Verified: `python -m unittest discover -v` — all 8 tests pass.