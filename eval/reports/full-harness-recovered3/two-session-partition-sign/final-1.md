Implemented `partition` with preserved order, duplicates, type hints, and no input mutation.

Added four passing unittest methods and documented design decisions and verification commands in `HANDOFF.md`.

Verification passed:
- `python -m py_compile solution.py test_solution.py`
- `python -m unittest discover -v` — 4 tests passed.