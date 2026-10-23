Implemented `runs` with type hints and without mutating input. Added six passing unittest regression tests and documented design decisions plus verification commands in `HANDOFF.md`.

Verified successfully:

- `python -m py_compile solution.py test_solution.py`
- `python -m unittest discover -v` — 6 tests passed.