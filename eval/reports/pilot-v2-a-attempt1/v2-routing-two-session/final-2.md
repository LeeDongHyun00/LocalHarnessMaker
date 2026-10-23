Implemented `run_many` and `render_many` using the day-1 APIs, preserving exact `routing` errors, ordering, trailing newlines, and independent results.

Added six batch regression tests. Protected files remain byte-for-byte unchanged; signatures and dependencies are unchanged.

Validation:
- `python verify.py`: **13 passed, 0 failed**; updated `verification.json`.
- `python -m unittest discover -v`: **13 passed, 0 failed**.

No requirements remain incomplete.