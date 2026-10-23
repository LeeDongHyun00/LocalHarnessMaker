Implemented runtime normalization through `project.policy.normalize`, corrected integer validation and rendering’s trailing newline, and added regressions including `test_domain_edge`.

Ran `python verify.py`: **7 passed, 0 failed**. Generated [verification.json](verification.json).

All four protected files remain byte-for-byte unchanged. Incomplete requirements: none.