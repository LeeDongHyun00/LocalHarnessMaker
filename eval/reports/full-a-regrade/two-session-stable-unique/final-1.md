Implemented `unique` with type hints, first-occurrence ordering, case-sensitive equality, and no input mutation.

Added 6 regression tests and recorded design decisions plus the verification command in `HANDOFF.md`.

Verified: `python -m unittest discover -v` — all 6 tests passed on Python 3.13.5.