Implemented canonicalization, duplicate handling, Kahn-wave ordering, and shared runtime `engine.compute` dispatch. Added regression coverage for both batch APIs and confirmed protected files are byte-for-byte unchanged.

Ran `python verify.py`: **10 passed, 0 failed**. Generated [verification.json](verification.json).

Incomplete requirements: none.