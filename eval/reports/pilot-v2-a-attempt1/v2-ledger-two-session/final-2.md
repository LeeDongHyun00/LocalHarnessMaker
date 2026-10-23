Implemented `run_many` and `render_many`, preserving day-1 policy, exact `ledger:` errors, signatures, and independent results. Added batch unittest coverage; all four protected files remain byte-for-byte unchanged.

- `python verify.py`: **12 passed, 0 failed**; regenerated `verification.json`.
- `python -m unittest discover -v`: **12 passed, 0 failed**.

No remaining requirements.