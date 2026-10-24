Implemented casefold normalization, deny-first tie resolution, idempotent duplicates, and shared runtime `engine.compute` delegation. Added regression coverage for both batch APIs.

Ran `python verify.py`: **10 passed, 0 failed**. Generated [verification.json](verification.json).

All four protected files remain byte-for-byte unchanged. No incomplete requirements.