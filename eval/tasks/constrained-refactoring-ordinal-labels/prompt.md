Refactor ordinal and ordinal_legacy to delegate their shared algorithm to one private helper. Preserve both signatures, return types, error behavior and input immutability. Keep imports and public names compatible.

Work only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.

Public behavior:
Format a nonnegative integer with its English ordinal suffix: 1st, 2nd, 3rd, 4th; 11,12,13 use th, including 111,112,113. Raise ValueError for negatives. Zero is 0th.

Maintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.

Submission requirements: test_solution.py must contain at least 2 passing unittest test methods exercising the public API. Retain all behavior and compatibility requirements above.
