Implemented `windows` with type hints, positive-size validation, and no input mutation.

Added 5 unittest methods covering ordinary windows, boundary sizes, empty inputs, invalid sizes, and independent output lists.

Verified: `python -m unittest discover -v` — all 5 tests pass.