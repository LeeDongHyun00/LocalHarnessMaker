Implemented case-folded canonicalization, strict predecessor version ordering, and shared runtime `engine.compute` dispatch. Added regression coverage for both batch APIs and edge cases. Protected files remain byte-for-byte unchanged.

Ran `python verify.py`: **10 passed, 0 failed**. Generated [verification.json](verification.json).

Incomplete requirements: none.