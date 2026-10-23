Implemented `run_many` and `render_many` using the existing day-1 APIs, preserving exact errors, policy, signatures, and protected files. Added batch coverage for ordering, rendering, errors, immutability, and independent results.

Verification:
- `python verify.py`: **13 passed, 0 failed**; updated `verification.json`.
- `python -m unittest discover -v`: **13 passed, 0 failed**.