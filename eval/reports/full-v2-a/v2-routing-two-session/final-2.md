Implemented both batch APIs, preserving day-1 policy, exact errors, signatures, and protected files. Added coverage for ordering, rendering, validation, input preservation, and independent results.

Verification completed:

- `python -m unittest discover -v`: 10 passed, 0 failed.
- `python verify.py`: 10 passed, 0 failed.

Updated generated [verification.json](verification.json).