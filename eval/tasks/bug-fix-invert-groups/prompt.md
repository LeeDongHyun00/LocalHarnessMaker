Fix the incorrect behavior of invert without changing its signature. Add a small regression test in test_solution.py.

Work only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.

Public behavior:
Group input keys by their values. Each list of keys follows dictionary insertion order. Empty input returns {}.

Maintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.

Submission requirements: test_solution.py must contain at least 1 passing unittest test methods exercising the public API. Retain all behavior and compatibility requirements above.
