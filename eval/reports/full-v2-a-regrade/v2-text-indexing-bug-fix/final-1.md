Implemented canonical case folding, zero-count support, idempotent duplicate handling, and shared runtime `engine.compute` delegation. Added regression coverage for both batch APIs, validation precedence, and output independence.

Ran `python verify.py`: **10 passed, 0 failed**. Generated [verification.json](verification.json).

Protected files remain byte-for-byte unchanged. No incomplete requirements.