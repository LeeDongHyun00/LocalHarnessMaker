Implemented `windows` with preserved type hints and no input mutation. Added 5 passing regression tests and documented design decisions plus the verification command in `HANDOFF.md`.

Verified with `python -m unittest discover -v` on Python 3.13.5: all 5 tests passed.