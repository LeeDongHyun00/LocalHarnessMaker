Implemented `normalize` with type hints, converting CRLF and lone CR to LF while preserving all other characters and trailing newlines.

Added three unittest methods covering ordinary, boundary, and empty inputs.

Verified: `python -m unittest discover -v` — all 3 tests passed.