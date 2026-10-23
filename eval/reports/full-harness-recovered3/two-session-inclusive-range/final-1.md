Implemented `inclusive()` with typed, inclusive ascending and descending ranges, including singleton results for equal endpoints.

Added four passing unittest methods and documented design decisions and verification commands in HANDOFF.md.

Verified successfully:
- `python -m py_compile solution.py`
- `python -m unittest discover -v`