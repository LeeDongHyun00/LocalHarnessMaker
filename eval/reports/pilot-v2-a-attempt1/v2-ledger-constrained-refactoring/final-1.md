Centralized normalization in `project.policy.normalize`; all four entry points observe runtime patches. Added regression coverage, including `test_domain_edge`.

Ran `python verify.py`: **8 passed, 0 failed**. Generated [verification.json](verification.json).

Confirmed protected files remain byte-for-byte unchanged. Incomplete requirements: none.