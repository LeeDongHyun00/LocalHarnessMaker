Refactor strip_prefix and strip_prefix_legacy to delegate their shared algorithm to one private helper. Preserve both signatures, return types, error behavior and input immutability. Keep imports and public names compatible.

Work only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.

Public behavior:
Remove exactly one matching prefix. A nonmatching or empty prefix leaves text unchanged. Do not strip individual characters or repeated prefixes.

Maintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.

Submission requirements: test_solution.py must contain at least 2 passing unittest test methods exercising the public API. Retain all behavior and compatibility requirements above.
