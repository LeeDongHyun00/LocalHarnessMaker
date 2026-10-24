Implemented `run_many` and `render_many`, preserving day-1 policy, exact errors, signatures, and dependencies. Added batch tests for ordering, rendering, failures, input immutability, and independent results. All four protected files remain unchanged.

Verification:

- `python verify.py`: **12 passed, 0 failed**; updated `verification.json`.
- `python -m unittest discover -v`: **12 passed, 0 failed**.