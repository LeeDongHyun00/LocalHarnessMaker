Implemented `pairs` with type hints, overlapping output in input order, and no input mutation. Added six passing unittest tests and documented design decisions and verification commands in `HANDOFF.md`.

Both checks passed:

- `python -m py_compile solution.py`
- `python -m unittest discover -v`