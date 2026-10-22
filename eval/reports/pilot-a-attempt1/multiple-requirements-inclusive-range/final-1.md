Fixed `inclusive` to include both endpoints in ascending or descending order, with a singleton for equal endpoints. Preserved type hints and added the public specification docstring.

Added 5 regression tests covering ordering, equal endpoints, negative values, crossing zero, and unchanged inputs.

Verified: `python -m unittest discover -v` — all 5 tests passed.