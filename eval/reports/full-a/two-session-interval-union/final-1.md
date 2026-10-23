Implemented `union` with type hints, endpoint validation, sorted merging of overlapping or touching intervals, and no input mutation.

Added 7 regression test methods and recorded design decisions plus the verification command in `HANDOFF.md`.

Verified: `python -m unittest discover -v` — all 7 tests passed.