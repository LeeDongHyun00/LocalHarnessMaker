Fix the incorrect behavior of windows without changing its signature. Add a small regression test in test_solution.py.

Work only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.

Public behavior:
Return all contiguous windows of exactly size, advancing by one. Raise ValueError for size <= 0. A size exceeding length returns [].

Maintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.

Submission requirements: test_solution.py must contain at least 1 passing unittest test methods exercising the public API. Retain all behavior and compatibility requirements above.
