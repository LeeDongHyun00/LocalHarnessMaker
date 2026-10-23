Implemented typed, case-sensitive `common` without mutating inputs. Added 8 passing regression tests and documented design decisions and verification commands in `HANDOFF.md`.

Verified successfully:

- `python -m py_compile solution.py test_solution.py`
- `python -m unittest discover -v`