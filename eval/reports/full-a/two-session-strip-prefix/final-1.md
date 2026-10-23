Implemented `strip_prefix` with type hints using `str.removeprefix`.

Added 6 passing unittest methods covering matching, nonmatching, empty, repeated, character-set, and Unicode cases. Recorded design decisions and the verification command in `HANDOFF.md`.

Verified: `python -m unittest discover -v` — all 6 tests passed.