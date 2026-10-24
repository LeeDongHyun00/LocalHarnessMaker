Implemented runtime path canonicalization through `project.policy.normalize`, kept target normalization separate, and added regressions covering domain edges and all four entry points.

Ran `python verify.py`: **7 passed, 0 failed**. Generated [verification.json](verification.json).

Protected files remain byte-for-byte unchanged. Incomplete requirements: none.