Implemented `run_many` and `render_many`, preserving day-1 policy, exact errors, signatures and dependencies. Added batch coverage for ordering, rendering, failures, immutability and independent results. Protected files remain byte-for-byte unchanged.

Verification:
- `python -m unittest discover -v`: 15 passed, 0 failed.
- `python verify.py`: 15 passed, 0 failed; regenerated `verification.json`.