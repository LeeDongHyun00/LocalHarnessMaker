Implemented `round_robin` with type hints, preserving group order and leaving inputs unchanged.

Added 5 unittest methods covering ordinary, uneven, boundary, empty, and shared-group inputs.

Verified: `python -m unittest discover -v` — all 5 tests pass.