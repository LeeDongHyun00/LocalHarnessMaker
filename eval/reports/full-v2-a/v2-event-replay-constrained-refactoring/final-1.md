Consolidated the copied paths through dynamically resolved `engine.compute`. Added regression coverage for both batch APIs, validation, replay rules, and output independence. All four protected files remain byte-for-byte unchanged.

Ran `python verify.py`: **9 passed, 0 failed**. Generated [verification.json](verification.json).

Incomplete requirements: none.