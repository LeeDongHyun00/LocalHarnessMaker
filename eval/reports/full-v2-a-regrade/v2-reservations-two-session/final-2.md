Implemented `run_many` and `render_many`, preserving day-1 policy, exact errors, signatures, and protected files. Added batch coverage for ordering, empty inputs, failures, immutability, and independent results.

Validation:
- `python -m unittest discover -v`: 13 passed.
- `python verify.py`: 13 passed, 0 failed; updated `verification.json`.

No remaining requirements.