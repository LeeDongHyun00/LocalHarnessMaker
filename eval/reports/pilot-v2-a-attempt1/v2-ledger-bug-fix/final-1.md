Fixed canonicalization with `strip().casefold()` and made identical canonical duplicates idempotent. Added regressions covering domain edges, validation, rendering, batches, and input isolation. Protected files remain byte-for-byte unchanged.

Ran `python verify.py`: **10 passing tests, 0 failures**.

Generated report: [verification.json](verification.json).

Incomplete requirements: none.