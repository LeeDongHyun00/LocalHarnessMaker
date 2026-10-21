Repair clamp. Also add its public specification as a docstring, add regression tests in test_solution.py, and preserve input values and collection order as specified.

Work only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.

Public behavior:
Clamp value into the inclusive [low,high] range. Raise ValueError if low > high. Equal bounds are valid.

Maintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.
