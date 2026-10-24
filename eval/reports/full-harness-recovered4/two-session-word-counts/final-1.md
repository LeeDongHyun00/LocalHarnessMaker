Implemented `words()` with whitespace splitting, Unicode casefolding, and punctuation preservation.

Added six passing unittest methods and documented design decisions and verification commands in `HANDOFF.md`.

Verification passed:

- `python -m py_compile solution.py`
- `python -m unittest discover -v` — 6 tests passed.