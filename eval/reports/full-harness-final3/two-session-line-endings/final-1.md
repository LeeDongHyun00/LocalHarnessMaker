Implemented `normalize` with type hints, preserving all characters except CRLF and CR normalization, including trailing line breaks.

Added six passing unittest methods and documented design decisions and verification commands in `HANDOFF.md`.

Verified on Python 3.13.5:
- `python -m py_compile solution.py`
- `python -m unittest discover -v` — all six tests pass.