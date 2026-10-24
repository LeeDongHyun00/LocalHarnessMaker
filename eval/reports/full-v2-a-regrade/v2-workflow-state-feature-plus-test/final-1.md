Implemented both batch APIs, fixed the forbidden `0 -> 2` transition, and added regression coverage for priority handling, batch atomicity, normalization, immutability, and runtime compute delegation.

Ran `python verify.py`: **13 passed, 0 failed**. Generated [verification.json](verification.json). All four protected files remain byte-for-byte unchanged.

Incomplete requirements: none.