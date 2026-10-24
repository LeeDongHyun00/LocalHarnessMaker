Consolidated all facade paths through runtime-resolved `engine.compute`. Added regressions covering both batch APIs, error precedence, normalization, ordering, and output independence. Protected files remain byte-for-byte unchanged.

Ran `python verify.py`: **7 passed, 0 failed**. Generated [verification.json](verification.json).

Incomplete requirements: none.