Refactor inclusive and inclusive_legacy to delegate their shared algorithm to one private helper. Preserve both signatures, return types, error behavior and input immutability. Keep imports and public names compatible.

Work only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.

Public behavior:
Return all integers from start through stop, inclusive, stepping +1 or -1 as appropriate. Equal endpoints give a singleton.

Maintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.

Submission requirements: test_solution.py must contain at least 2 passing unittest test methods exercising the public API. Retain all behavior and compatibility requirements above.
