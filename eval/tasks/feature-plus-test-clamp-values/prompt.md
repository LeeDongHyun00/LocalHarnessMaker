Implement clamp and add standard-library unittest tests in test_solution.py covering ordinary, boundary and empty inputs (or invalid numeric inputs when no collection is accepted).

Work only in the supplied task workspace. Edit solution.py and public tests; use Python 3.11+ and the standard library. Do not access parent repositories or external services.

Public behavior:
Clamp value into the inclusive [low,high] range. Raise ValueError if low > high. Equal bounds are valid.

Maintain type hints. Do not mutate input collections. No algorithmic complexity constraint is imposed. Verify with python -m unittest discover -v.

Submission requirements: test_solution.py must contain at least 2 passing unittest test methods exercising the public API. Retain all behavior and compatibility requirements above.
